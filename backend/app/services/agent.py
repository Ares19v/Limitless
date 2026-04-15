"""
Agent mode — LangChain ReAct agent with 3 tools:
  1. search_document  — hybrid search in the current document
  2. web_search       — DuckDuckGo web search (no API key needed)
  3. calculate        — safe arithmetic evaluator

Streams intermediate reasoning steps + final answer via SSE.
"""

from __future__ import annotations

import json
import re
from typing import AsyncGenerator
from uuid import UUID

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.vector_store import hybrid_similarity_search

logger = get_logger(__name__)

AGENT_PROMPT = PromptTemplate.from_template("""You are Limitless, an intelligent AI agent with access to tools.
You help users understand documents and answer questions using real data.

You have access to the following tools:
{tools}

Use the following format EXACTLY:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}""")


def _make_tools(document_id: UUID):
    """Create document-scoped tools for the agent."""

    @tool
    def search_document(query: str) -> str:
        """Search the uploaded document for information relevant to the query. Use this first."""
        import asyncio
        chunks = asyncio.run(hybrid_similarity_search(document_id, query, top_k=5))
        if not chunks:
            return "No relevant content found in the document."
        parts = []
        for i, c in enumerate(chunks, 1):
            page = f" (Page {c.page})" if c.page else ""
            parts.append(f"[Excerpt {i}{page}]: {c.content[:500]}")
        return "\n\n".join(parts)

    @tool
    def web_search(query: str) -> str:
        """Search the internet for real-time or external information not in the document."""
        try:
            from duckduckgo_search import DDGS
            results = list(DDGS().text(query, max_results=3))
            if not results:
                return "No web results found."
            parts = [f"• {r['title']}: {r['body']}" for r in results]
            return "\n".join(parts)
        except Exception as e:
            return f"Web search unavailable: {str(e)}"

    @tool
    def calculate(expression: str) -> str:
        """Evaluate a safe mathematical expression. E.g. '2 + 2', '100 * 0.05', 'sqrt(144)'."""
        import math
        try:
            safe_expr = re.sub(r"[^0-9+\-*/().,\s]", "", expression)
            allowed = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
            result = eval(safe_expr, {"__builtins__": {}}, allowed)
            return str(result)
        except Exception as e:
            return f"Calculation error: {e}"

    return [search_document, web_search, calculate]


async def stream_agent_response(
    document_id: UUID,
    user_message: str,
) -> AsyncGenerator[str, None]:
    """
    Run the ReAct agent and stream steps + final answer via SSE.
    Each tool call is surfaced as a live update in the UI.
    """
    settings = get_settings()

    llm = ChatGroq(
        model=settings.llm_model,
        groq_api_key=settings.groq_api_key,
        temperature=0.1,
        max_tokens=2048,
    )

    tools = _make_tools(document_id)
    agent = create_react_agent(llm, tools, AGENT_PROMPT)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        max_iterations=5,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    logger.info("agent_start", document_id=str(document_id))

    try:
        result = await executor.ainvoke({"input": user_message})

        # Stream intermediate steps (tool calls)
        steps = result.get("intermediate_steps", [])
        for action, observation in steps:
            tool_name = action.tool
            tool_input = action.tool_input
            emoji = {"search_document": "🔍", "web_search": "🌐", "calculate": "🧮"}.get(tool_name, "🔧")
            step_data = {
                "type": "step",
                "tool": tool_name,
                "input": str(tool_input)[:200],
                "emoji": emoji,
            }
            yield f"event: step\ndata: {json.dumps(step_data)}\n\n"

        # Stream final answer token-like (send as one block)
        final = result.get("output", "I could not determine an answer.")
        yield f"data: {final}\n\n"

    except Exception as exc:
        logger.error("agent_error", error=str(exc))
        yield f"data: ❌ Agent error: {str(exc)}\n\n"

    finally:
        yield "event: done\ndata: [DONE]\n\n"
        logger.info("agent_complete", document_id=str(document_id))
