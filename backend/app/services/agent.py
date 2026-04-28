"""
Agent mode — LangChain ReAct agent with 3 tools.
FIX: Tools run in a separate thread pool with their own event loop,
     avoiding the 'asyncio.run() inside running loop' crash.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
from typing import AsyncGenerator
from uuid import UUID

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.key_manager import get_llm as get_groq_llm
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


def _run_in_new_loop(coro):
    """Run an async coroutine in a fresh thread with its own event loop.
    This avoids 'asyncio.run() called inside running loop' errors."""
    def _thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_thread_target)
        return future.result(timeout=30)


def _make_tools(document_id: UUID):
    """Create document-scoped tools for the agent."""

    @tool
    def search_document(query: str) -> str:
        """Search the uploaded document for information relevant to the query. Use this first for any document question."""
        try:
            chunks = _run_in_new_loop(hybrid_similarity_search(document_id, query, top_k=5))
            if not chunks:
                return "No relevant content found in the document."
            parts = []
            for i, c in enumerate(chunks, 1):
                page = f" (Page {c.page})" if c.page else ""
                parts.append(f"[Excerpt {i}{page}]: {c.content[:500]}")
            return "\n\n".join(parts)
        except Exception as e:
            logger.error("agent_search_doc_error", error=str(e))
            return f"Document search failed: {str(e)}"

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
            logger.error("agent_web_search_error", error=str(e))
            return f"Web search unavailable: {str(e)}"

    @tool
    def calculate(expression: str) -> str:
        """Evaluate a safe mathematical expression. E.g. '2 + 2', '100 * 0.05', 'sqrt(16)'."""
        import ast
        import math
        import operator

        _SAFE_OPS = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
            ast.Mod: operator.mod,
            ast.FloorDiv: operator.floordiv,
        }
        _SAFE_FUNCS = {
            name: getattr(math, name)
            for name in ("sqrt", "log", "log2", "log10", "exp", "sin", "cos", "tan",
                         "asin", "acos", "atan", "atan2", "ceil", "floor", "fabs",
                         "factorial", "gcd", "degrees", "radians", "pi", "e")
            if hasattr(math, name)
        }

        def _eval(node):
            if isinstance(node, ast.Constant):
                if not isinstance(node.value, (int, float)):
                    raise ValueError(f"Unsupported constant type: {type(node.value)}")
                return node.value
            elif isinstance(node, ast.BinOp):
                op_type = type(node.op)
                if op_type not in _SAFE_OPS:
                    raise ValueError(f"Unsupported operator: {op_type.__name__}")
                left = _eval(node.left)
                right = _eval(node.right)
                return _SAFE_OPS[op_type](left, right)
            elif isinstance(node, ast.UnaryOp):
                op_type = type(node.op)
                if op_type not in _SAFE_OPS:
                    raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
                return _SAFE_OPS[op_type](_eval(node.operand))
            elif isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in _SAFE_FUNCS:
                    raise ValueError(f"Unsupported function call: {getattr(node.func, 'id', '?')}")
                args = [_eval(a) for a in node.args]
                return _SAFE_FUNCS[node.func.id](*args)
            elif isinstance(node, ast.Name):
                if node.id in _SAFE_FUNCS:
                    return _SAFE_FUNCS[node.id]
                raise ValueError(f"Unknown name: {node.id}")
            else:
                raise ValueError(f"Unsupported expression node: {type(node).__name__}")

        try:
            tree = ast.parse(expression.strip(), mode="eval")
            result = _eval(tree.body)
            return str(round(result, 10) if isinstance(result, float) else result)
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

    llm = get_groq_llm(streaming=False, temperature=0.1, max_tokens=2048)

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

        # Stream intermediate steps (tool calls) first
        steps = result.get("intermediate_steps", [])
        for action, observation in steps:
            tool_name = getattr(action, "tool", "unknown")
            tool_input = getattr(action, "tool_input", "")
            emoji = {"search_document": "🔍", "web_search": "🌐", "calculate": "🧮"}.get(tool_name, "🔧")
            step_data = {
                "type": "step",
                "tool": tool_name,
                "input": str(tool_input)[:200],
                "emoji": emoji,
            }
            yield f"event: step\ndata: {json.dumps(step_data)}\n\n"

        # Final answer
        final = result.get("output", "I could not determine an answer.")
        yield f"data: {final}\n\n"

    except Exception as exc:
        logger.error("agent_error", error=str(exc))
        yield f"data: ❌ Agent error: {str(exc)}\n\n"

    finally:
        yield "event: done\ndata: [DONE]\n\n"
        logger.info("agent_complete", document_id=str(document_id))
