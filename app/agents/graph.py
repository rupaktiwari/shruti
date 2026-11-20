from langgraph.graph import END, StateGraph

from app.agents.router import router_node
from app.agents.state import ShrutiState
from app.schemas.booking import BookingDetails
from app.services.booking_rules import REQUIRED_FIELDS, ROOM_CAPACITY
from app.services.booking_service import extract_booking_intent, save_booking, slots_left
from app.services.escalation_service import escalate
from app.services.language import prefers_nepali
from app.services.llm_service import llm
from app.services.rag_service import retrieve


def _history_text(history: list[dict]) -> str:
    return "\n".join(f"{turn['role']}: {turn['content']}" for turn in history)


def _language_rule(transcript: str) -> str:
    if prefers_nepali(transcript):
        return "Reply in Nepali. Keep names, emails, dates, and room types as given."
    return "Reply in English. Keep names, emails, dates, and room types as given."


def _retrieval_query(state: ShrutiState) -> str:
    earlier = " ".join(
        turn["content"] for turn in state.get("history") or [] if turn.get("role") == "user"
    )
    return f"{state['transcript']}\n{earlier}".strip()


def rag_node(state: ShrutiState) -> ShrutiState:
    context = retrieve(_retrieval_query(state))
    if context is None:
        return {**state, "route": "escalate"}

    prompt = f"""You are Shruti, the concierge at Himalaya House, a resort in Pokhara.
Answer only from the context. Nightly rates in the context are the room price.
If the guest gave dates, nights are check-out minus check-in. Quote the nightly rate and the stay total before VAT, and mention the 13 percent VAT.
Do not say the price is missing when a nightly rate for that room is in the context.
If the context does not contain the answer, say you do not know.
{_language_rule(state["transcript"])}

Context:
{context}

Conversation so far:
{_history_text(state["history"])}

Guest: {state["transcript"]}
"""
    answer = llm.invoke(prompt).content.strip()
    return {**state, "answer": answer}


def general_node(state: ShrutiState) -> ShrutiState:
    prompt = f"""You are Shruti, the concierge at Himalaya House in Pokhara.
Answer the guest briefly. If the question is not about the resort, answer it and offer to help with a stay.
{_language_rule(state["transcript"])}

Conversation so far:
{_history_text(state["history"])}

Guest: {state["transcript"]}
"""
    answer = llm.invoke(prompt).content.strip()
    return {**state, "answer": answer}


def escalate_node(state: ShrutiState) -> ShrutiState:
    answer = escalate(state["transcript"], state["session_id"])
    return {**state, "answer": answer}


def booking_node(state: ShrutiState) -> ShrutiState:
    conversation = _history_text(state["history"])
    conversation = f"{conversation}\nguest: {state['transcript']}".strip()
    info = extract_booking_intent(conversation)
    nepali = prefers_nepali(state["transcript"])

    if not info.get("wants_booking"):
        reply = (
            "कोठा बुक गर्न नाम, इमेल, चेक-इन, चेक-आउट, पाहुना संख्या र कोठाको प्रकार भन्नुहोस्।"
            if nepali
            else "I can book a room. Tell me your name, email, check-in, check-out, number of guests, and room type (standard, deluxe, or suite)."
        )
        return {**state, "answer": reply}

    room_type = info.get("room_type")
    check_in = info.get("check_in")
    check_out = info.get("check_out")
    availability_note = ""
    if room_type and check_in and check_out:
        remaining = slots_left(room_type, check_in, check_out)
        if remaining is None:
            availability_note = ""
        elif remaining <= 0:
            reply = (
                f"{room_type} कोठा ती मितिमा खाली छैन। अर्को कोठा वा अर्को मिति रोज्नुहोस्।"
                if nepali
                else f"The {room_type} rooms are full for those dates. Try another room type or different dates."
            )
            return {**state, "answer": reply}
        else:
            availability_note = (
                f"{room_type} खाली छ ({remaining} कोठा)। "
                if nepali
                else f"A {room_type} room is free for those dates ({remaining} left). "
            )

    missing = [field for field in REQUIRED_FIELDS if not info.get(field)]
    if missing:
        fields = ", ".join(missing)
        reply = (
            f"{availability_note}बुक गर्न अझै चाहिन्छ: {fields}।"
            if nepali
            else f"{availability_note}To finish the booking I still need: {fields}."
        )
        return {**state, "answer": reply}

    try:
        details = BookingDetails(
            name=info["name"],
            email=info["email"],
            check_in=info["check_in"],
            check_out=info["check_out"],
            guests=int(info["guests"]),
            room_type=info["room_type"],
        )
    except (TypeError, ValueError):
        reply = (
            "इमेल वा मिति मिलेन। मिति YYYY-MM-DD मा लेख्नुहोस्।"
            if nepali
            else "I couldn't validate that. Please check the email and use dates as YYYY-MM-DD."
        )
        return {**state, "answer": reply}

    if details.guests > ROOM_CAPACITY[details.room_type]:
        limit = ROOM_CAPACITY[details.room_type]
        reply = (
            f"{details.room_type} मा बढीमा {limit} जना बस्न मिल्छ।"
            if nepali
            else f"A {details.room_type} room holds at most {limit} guests."
        )
        return {**state, "answer": reply}

    outcome = save_booking(details)
    if outcome == "created":
        reply = (
            f"बुक भयो। {details.name}, {details.room_type}, {details.check_in} देखि {details.check_out}, "
            f"{details.guests} जना। पुष्टि {details.email} मा जान्छ। भुक्तानी आउँदा फ्रन्ट डेस्कमा हुन्छ।"
            if nepali
            else (
                f"Booked. {details.name}, {details.room_type}, {details.check_in} to {details.check_out}, "
                f"{details.guests} guest(s). A confirmation will go to {details.email}. "
                "Payment is collected at the front desk on arrival."
            )
        )
    elif outcome == "duplicate":
        reply = (
            f"{details.email} का लागि {details.check_in} देखि {details.check_out} पहिले नै बुक छ।"
            if nepali
            else f"You already have a stay booked for {details.check_in} to {details.check_out} under {details.email}."
        )
    elif outcome == "unavailable":
        reply = (
            f"{details.room_type} ती मितिमा खाली छैन।"
            if nepali
            else f"The {details.room_type} rooms are full for those dates."
        )
    else:
        reply = (
            "मिति वा कोठा मिलेन। चेक-आउट चेक-इनभन्दा पछि हुनुपर्छ। कोठा: standard, deluxe, suite।"
            if nepali
            else "Those dates or that room type don't work. Check-out must be after check-in. Room types are standard, deluxe, and suite."
        )
    return {**state, "answer": reply}


def route_decision(state: ShrutiState) -> str:
    return state["route"] or "escalate"


def build_graph():
    graph = StateGraph(ShrutiState)
    graph.add_node("router", router_node)
    graph.add_node("rag", rag_node)
    graph.add_node("booking", booking_node)
    graph.add_node("general", general_node)
    graph.add_node("escalate", escalate_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "rag": "rag",
            "booking": "booking",
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
    graph.add_edge("booking", END)
    graph.add_edge("general", END)
    graph.add_edge("escalate", END)
    return graph.compile()
