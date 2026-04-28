"""
Agent mode — manual ReAct loop using Groq LLM directly.
Replaces the old LangChain AgentExecutor which broke in langchain 1.x.

The agent is implemented as a simple Thought/Action/Observation loop:
1. LLM decides which tool to call (if any)
2. We parse the output and run the tool
3. Feed the observation back and repeat (max 5 iterations)
4. Stream steps + final answer via SSE
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
from typing import AsyncGenerator
from uuid import UUID

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.key_manager import get_llm as get_groq_llm
from app.services.vector_store import hybrid_similarity_search

logger = get_logger(__name__)


# ── Tool definitions ──────────────────────────────────────────────────────────

def _run_in_new_loop(coro):
    """Run an async coroutine in a fresh thread with its own event loop.
    Avoids 'asyncio.run() called inside running loop' errors."""
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


def _tool_search_document(document_id: UUID, query: str) -> str:
    """Search the uploaded document for relevant information."""
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


def _tool_web_search(query: str) -> str:
    """Search the internet for real-time information."""
    try:
        from duckduckgo_search import DDGS
        results = list(DDGS().text(query, max_results=3))
        if not results:
            return "No web results found."
        return "\n".join(f"• {r['title']}: {r['body']}" for r in results)
    except Exception as e:
        logger.error("agent_web_search_error", error=str(e))
        return f"Web search unavailable: {str(e)}"


def _tool_calculate(expression: str) -> str:
    """Evaluate a safe mathematical expression."""
    import ast
    import math
    import operator

    _SAFE_OPS = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.UAdd: operator.pos, ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
    }
    _SAFE_FUNCS = {
        name: getattr(math, name)
        for name in ("sqrt", "log", "log2", "log10", "exp", "sin", "cos", "tan",
                     "ceil", "floor", "fabs", "factorial", "pi", "e")
        if hasattr(math, name)
    }

    def _eval(node):
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ValueError(f"Unsupported type: {type(node.value)}")
            return node.value
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPS:
                raise ValueError(f"Unsupported op: {op_type.__name__}")
            return _SAFE_OPS[op_type](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPS:
                raise ValueError(f"Unsupported unary op: {op_type.__name__}")
            return _SAFE_OPS[op_type](_eval(node.operand))
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _SAFE_FUNCS:
                raise ValueError(f"Unsupported function: {getattr(node.func, 'id', '?')}")
            return _SAFE_FUNCS[node.func.id](*[_eval(a) for a in node.args])
        elif isinstance(node, ast.Name):
            if node.id in _SAFE_FUNCS:
                return _SAFE_FUNCS[node.id]
            raise ValueError(f"Unknown name: {node.id}")
        else:
            raise ValueError(f"Unsupported node: {type(node).__name__}")

    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _eval(tree.body)
        return str(round(result, 10) if isinstance(result, float) else result)
    except Exception as e:
        return f"Calculation error: {e}"


# ── ReAct system prompt ───────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are Limitless, an intelligent AI agent with access to tools.

You have access to these tools:
- search_document(query): Search the uploaded document for relevant information. Use this FIRST for any document question.
- web_search(query): Search the internet for real-time or external information.
- calculate(expression): Evaluate a mathematical expression (e.g. "2 + 2", "sqrt(16)").

Respond using EXACTLY this format:
Thought: <your reasoning about what to do>
Action: <tool_name>
Action Input: <input to the tool>

After receiving an Observation, continue with another Thought/Action/Action Input OR give a final answer:
Thought: I now know the final answer.
Final Answer: <your complete answer to the user>

Only use "Final Answer:" when you are ready to give the complete response.
"""

_TOOL_EMOJIS = {
    "search_document": "🔍",
    "web_search": "🌐",
    "calculate": "🧮",
}


def _parse_action(text: str):
    """Parse Action and Action Input from LLM output. Returns (tool_name, tool_input) or None."""
    import re
    action_match = re.search(r"Action:\s*(\w+)", text)
    input_match = re.search(r"Action Input:\s*(.+?)(?:\n|$)", text, re.DOTALL)
    if action_match and input_match:
        return action_match.group(1).strip(), input_match.group(1).strip()
    return None


def _parse_final_answer(text: str):
    """Extract the Final Answer from LLM output."""
    import re
    match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


# ── Main agent function ───────────────────────────────────────────────────────

async def stream_agent_response(
    document_id: UUID,
    user_message: str,
) -> AsyncGenerator[str, None]:
    """
    Run the ReAct agent loop and stream steps + final answer via SSE.
    Implements the loop manually without LangChain AgentExecutor.
    """
    llm = get_groq_llm(streaming=False, temperature=0.1, max_tokens=2048)
    logger.info("agent_start", document_id=str(document_id))

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    max_iterations = 5

    try:
        for iteration in range(max_iterations):
            # Call LLM
            response = await llm.ainvoke(messages)
            llm_text = response.content.strip()

            # Check for final answer first
            final_answer = _parse_final_answer(llm_text)
            if final_answer:
                yield f"data: {final_answer}\n\n"
                break

            # Parse tool call
            parsed = _parse_action(llm_text)
            if not parsed:
                # No structured action found — treat raw output as final answer
                yield f"data: {llm_text}\n\n"
                break

            tool_name, tool_input = parsed
            emoji = _TOOL_EMOJIS.get(tool_name, "🔧")

            # Stream the step to the frontend
            step_data = {
                "type": "step",
                "tool": tool_name,
                "input": str(tool_input)[:200],
                "emoji": emoji,
            }
            yield f"event: step\ndata: {json.dumps(step_data)}\n\n"

            # Execute the tool
            loop = asyncio.get_event_loop()
            if tool_name == "search_document":
                observation = await loop.run_in_executor(
                    None, lambda q=tool_input: _tool_search_document(document_id, q)
                )
            elif tool_name == "web_search":
                observation = await loop.run_in_executor(
                    None, lambda q=tool_input: _tool_web_search(q)
                )
            elif tool_name == "calculate":
                observation = _tool_calculate(tool_input)
            else:
                observation = f"Unknown tool: {tool_name}"

            logger.info("agent_tool_result", tool=tool_name, obs_len=len(observation))

            # Feed observation back to the conversation
            messages.append({"role": "assistant", "content": llm_text})
            messages.append({
                "role": "user",
                "content": f"Observation: {observation}\n\nContinue reasoning."
            })
        else:
            # Max iterations reached
            yield "data: I reached the maximum number of reasoning steps. Here is what I found so far.\n\n"

    except Exception as exc:
        logger.error("agent_error", error=str(exc))
        yield f"data: ❌ Agent error: {str(exc)}\n\n"

    finally:
        yield "event: done\ndata: [DONE]\n\n"
        logger.info("agent_complete", document_id=str(document_id))
