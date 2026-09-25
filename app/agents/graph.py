# app/agents/graph.py
import sqlite3

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

from app.agents.router import router_node
from app.agents.state import ShrutiState
from app.services.escalation_service import escalate
from app.services.llm_service import llm
from app.services.rag_service import rag_service


NEPALI_RESPONSE_RULE = """
Respond only in Nepali.
Do not respond in English.
Preserve important numbers, names, URLs, and necessary technical terms.
"""


def rag_node(state: ShrutiState) -> ShrutiState:
    context = rag_service.retrieve(state["transcript"])

    if context is None:
        return {**state, "route": "escalate"}

    prompt = f"""
You are a Nepali financial customer-support assistant.

Use ONLY the context provided below. Do not invent information.

{NEPALI_RESPONSE_RULE}

Context:
{context}

User's question:
{state["transcript"]}

Write a clear and helpful answer in Nepali.
"""

    answer = llm.invoke(prompt).content.strip()

    return {
        **state,
        "answer": answer,
    }


def general_node(state: ShrutiState) -> ShrutiState:
    prompt = f"""
You are a helpful Nepali conversational assistant.

{NEPALI_RESPONSE_RULE}

User's question:
{state["transcript"]}

Answer naturally and clearly in Nepali.
"""

    answer = llm.invoke(prompt).content.strip()

    return {
        **state,
        "answer": answer,
    }


def escalate_node(state: ShrutiState) -> ShrutiState:
    answer = escalate(
        state["transcript"],
        state["thread_id"],
    )

    return {
        **state,
        "answer": answer,
    }


def route_decision(state: ShrutiState) -> str:
    return state["route"]


def build_graph():
    graph = StateGraph(ShrutiState)

    graph.add_node("router", router_node)
    graph.add_node("rag", rag_node)
    graph.add_node("general", general_node)
    graph.add_node("escalate", escalate_node)

    graph.set_entry_point("router")

    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "rag": "rag",
            "general": "general",
            "escalate": "escalate",
        },
    )

    graph.add_conditional_edges(
        "rag",
        route_decision,
        {
            "escalate": "escalate",
            "rag": END,
        },
    )

    graph.add_edge("general", END)
    graph.add_edge("escalate", END)

    conn = sqlite3.connect(
        "shruti_conversations.db",
        check_same_thread=False,
    )
    checkpointer = SqliteSaver(conn)

    return graph.compile(checkpointer=checkpointer)