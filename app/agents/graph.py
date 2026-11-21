from langgraph.graph import END, StateGraph

from app.agents.state import TurnState
from app.services.llm_service import llm
from app.services.rag_service import retrieve
from app.services.replies import empty_notebook_reply, language_rule, missing_source_reply


def _history_text(history: list[dict], limit: int = 8) -> str:
    lines = []
    for turn in history[-limit:]:
        content = (turn.get("content") or "")[:2000]
        lines.append(f"{turn.get('role', 'user')}: {content}")
    return "\n".join(lines)


def _retrieval_query(state: TurnState) -> str:
    earlier = " ".join(
        turn["content"]
        for turn in (state.get("history") or [])[-4:]
        if turn.get("role") == "user"
    )
    query = f"{state['transcript']}\n{earlier}".strip()
    return query[:1500]


def _enter(state: TurnState) -> TurnState:
    return state


def _choose_mode(state: TurnState) -> str:
    return "chat" if state["mode"] == "shruti" else "retrieve"


def chat_node(state: TurnState) -> TurnState:
    prompt = f"""You are Shruti, a general assistant.
Answer the user directly. You cannot see uploaded files. If they ask about a file they uploaded, tell them to open Smriti, the notebook, and ask there.
{language_rule(state["transcript"])}

Conversation so far:
{_history_text(state["history"])}

User: {state["transcript"]}
"""
    answer = llm.invoke(prompt).content.strip()
    return {**state, "route": "chat", "answer": answer, "citations": []}


def retrieve_node(state: TurnState) -> TurnState:
    context, citations, point_count = retrieve(
        _retrieval_query(state),
        notebook_id=state["notebook_id"],
    )
    if point_count == 0:
        return {
            **state,
            "route": "empty",
            "context": None,
            "citations": [],
            "answer": empty_notebook_reply(state["transcript"]),
        }
    if not context:
        return {
            **state,
            "route": "empty",
            "context": None,
            "citations": [],
            "answer": missing_source_reply(state["transcript"]),
        }
    return {**state, "route": "answer", "context": context, "citations": citations}


def answer_node(state: TurnState) -> TurnState:
    prompt = f"""You are Smriti. You answer questions about one notebook.
Use only the excerpts below. After a claim, cite the filename in square brackets, exactly as written, for example [notes.txt].
If the excerpts do not contain the answer, say it is not in this notebook. Do not add facts from outside the excerpts.
{language_rule(state["transcript"])}

Excerpts:
{state["context"]}

Conversation so far:
{_history_text(state["history"])}

Question: {state["transcript"]}
"""
    answer = llm.invoke(prompt).content.strip()
    return {**state, "answer": answer}


def route_after_retrieve(state: TurnState) -> str:
    return "empty" if state["route"] == "empty" else "answer"


def build_graph():
    graph = StateGraph(TurnState)
    graph.add_node("enter", _enter)
    graph.add_node("chat", chat_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("answer", answer_node)

    graph.set_entry_point("enter")
    graph.add_conditional_edges(
        "enter",
        _choose_mode,
        {"chat": "chat", "retrieve": "retrieve"},
    )
    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {"answer": "answer", "empty": END},
    )
    graph.add_edge("chat", END)
    graph.add_edge("answer", END)
    return graph.compile()
