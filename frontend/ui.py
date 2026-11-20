import os
import uuid

import requests
import streamlit as st

API_URL = os.getenv("SHRUTI_API_URL", "http://127.0.0.1:8000")

ROUTE_LABELS = {
    "rag": "Resort notes",
    "booking": "Reservation",
    "general": "General",
    "escalate": "Front desk",
}

SUGGESTIONS = [
    ("Check-in and breakfast", "What time is check-in, and when is breakfast?"),
    ("Deluxe room rate", "How much is a deluxe room, and what does it include?"),
    ("From the airport", "How do I get to the property from the airport?"),
    ("Hold a deluxe room", "Book a deluxe room for Sita Sharma, sita@example.com, check-in 2026-12-12, check-out 2026-12-15, 2 guests."),
]

st.set_page_config(
    page_title="Shruti",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,460;9..144,600&family=Outfit:wght@380;500;600&display=swap');

    html, body, [data-testid="stAppViewContainer"], .stApp {
        background: #f4efe6;
        color: #1c1915;
        font-family: "Outfit", sans-serif;
    }
    .main .block-container {
        max-width: 860px;
        padding-top: 1.4rem;
        padding-bottom: 7rem;
    }
    h1, h2, h3, .hero-title {
        font-family: "Fraunces", serif !important;
        letter-spacing: -0.03em;
    }
    section[data-testid="stSidebar"] {
        background: #1f3d32;
        border-right: 0;
    }
    section[data-testid="stSidebar"] * {
        color: #f4efe6 !important;
        font-family: "Outfit", sans-serif;
    }
    section[data-testid="stSidebar"] [data-testid="stIconMaterial"] {
        font-family: "Material Symbols Rounded" !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(244, 239, 230, 0.18);
    }
    section[data-testid="stSidebar"] button {
        background: transparent !important;
        border: 1px solid rgba(244, 239, 230, 0.22) !important;
        color: #f4efe6 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        border-radius: 12px !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background: rgba(244, 239, 230, 0.08) !important;
        border-color: rgba(244, 239, 230, 0.45) !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"] {
        background: #f4efe6 !important;
        color: #1f3d32 !important;
        border: 0 !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"] * {
        color: #1f3d32 !important;
    }
    div[data-testid="stChatMessage"] {
        background: transparent;
        border-radius: 18px;
        padding: 0.35rem 0.2rem;
    }
    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
    div[data-testid="stChatMessage"]:has(span[data-testid="chatAvatarIcon-assistant"]) {
        background: rgba(31, 61, 50, 0.06);
        padding: 0.7rem 0.85rem;
    }
    div[data-testid="stChatInput"] textarea {
        border-radius: 18px !important;
        border: 1px solid #d9d0c2 !important;
        background: #fffdf8 !important;
        font-family: "Outfit", sans-serif !important;
    }
    .main .stButton button {
        background: #fffdf8 !important;
        color: #1c1915 !important;
        border: 1px solid #ddd4c6 !important;
        border-radius: 16px !important;
        min-height: 4.4rem;
        height: auto !important;
        white-space: normal !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 0.85rem 1rem !important;
        font-family: "Outfit", sans-serif !important;
        line-height: 1.35 !important;
    }
    .main .stButton button:hover {
        border-color: #1f3d32 !important;
        background: #fff !important;
    }
    section.stMain [data-testid="stMainBlockContainer"] {
        padding-bottom: 6.5rem;
    }
    section.stMain [data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]) {
        position: fixed;
        bottom: 1rem;
        left: 50%;
        transform: translateX(calc(-50% + 150px));
        width: min(860px, calc(100vw - 22rem));
        z-index: 30;
        margin: 0;
        align-items: center;
        background: #f4efe6;
        padding: 0.35rem 0;
    }
    section.stMain [data-testid="stPopover"] button {
        background: #1f3d32 !important;
        color: #f4efe6 !important;
        border: 0 !important;
        border-radius: 16px !important;
        min-height: 3.15rem !important;
        height: 3.15rem !important;
        justify-content: center !important;
        text-align: center !important;
        font-family: "Outfit", sans-serif !important;
        font-weight: 500 !important;
    }
    section.stMain [data-testid="stPopover"] button * {
        color: #f4efe6 !important;
    }
    .offline-note {
        margin-top: 1rem;
        padding: 0.75rem 0.9rem;
        border-radius: 12px;
        background: #f6e7d8;
        color: #6a3b16;
        font-size: 0.95rem;
    }
    .hero-kicker {
        letter-spacing: 0.18em;
        text-transform: uppercase;
        font-size: 0.74rem;
        color: #6d6458;
        margin-bottom: 0.4rem;
    }
    .hero-title {
        font-size: 3.4rem;
        line-height: 0.95;
        margin: 0;
        color: #1f3d32;
    }
    .hero-copy {
        font-size: 1.08rem;
        color: #4d463d;
        max-width: 38rem;
        margin-top: 0.8rem;
    }
    .pill {
        display: inline-block;
        border-radius: 999px;
        padding: 0.12rem 0.55rem;
        font-size: 0.75rem;
        letter-spacing: 0.04em;
        background: #e7efe9;
        color: #1f3d32;
        border: 1px solid #c9d9cf;
    }
    .status-ok { color: #d7ecdf !important; }
    .status-off { color: #f0d7c4 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

defaults = {
    "messages": [],
    "thread_id": f"stay-{uuid.uuid4().hex[:10]}",
    "pending_transcript": None,
    "pending_audio": None,
    "widget_key": 0,
    "confirm_delete": None,
}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)


def api_health():
    try:
        response = requests.get(f"{API_URL}/", timeout=3)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        return None
    return None


def transcribe_only(audio_bytes):
    files = {"file": ("voice.wav", audio_bytes, "audio/wav")}
    response = requests.post(f"{API_URL}/transcribe", files=files, timeout=300)
    if response.status_code != 200:
        st.error("Transcription failed. The quantized speech model may still be loading.")
        return None
    return response.json().get("transcription", "").strip()


def send_to_shruti(transcript):
    response = requests.post(
        f"{API_URL}/converse",
        json={"transcript": transcript, "thread_id": st.session_state.thread_id},
        timeout=300,
    )
    if response.status_code != 200:
        st.error("Shruti could not answer just now. Check that the API and Groq key are running.")
        return None, None
    result = response.json()
    return result.get("answer", ""), result.get("route", "")


def fetch_threads():
    try:
        payload = requests.get(f"{API_URL}/conversations", timeout=10).json()
        return payload if isinstance(payload, list) else []
    except requests.exceptions.RequestException:
        return []


def fetch_reservations():
    try:
        payload = requests.get(f"{API_URL}/reservations", timeout=10).json()
        return payload if isinstance(payload, list) else []
    except requests.exceptions.RequestException:
        return []


def delete_thread(thread_id):
    try:
        response = requests.delete(f"{API_URL}/conversations/{thread_id}", timeout=10)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        st.error("Could not reach the server to delete this conversation.")
        return False


def start_new_conversation():
    st.session_state.messages = []
    st.session_state.thread_id = f"stay-{uuid.uuid4().hex[:10]}"
    st.session_state.pending_transcript = None
    st.session_state.pending_audio = None
    st.session_state.widget_key += 1


def load_thread(thread_id):
    st.session_state.thread_id = thread_id
    history = requests.get(f"{API_URL}/conversations/{thread_id}", timeout=10).json()
    st.session_state.messages = [
        {"role": item["role"], "content": item["content"], "route": item.get("route"), "audio": None}
        for item in history
    ]
    st.session_state.pending_transcript = None
    st.session_state.pending_audio = None


def send_message(content, audio=None):
    content = content.strip()
    if not content:
        return
    st.session_state.messages.append({"role": "user", "content": content, "audio": audio})
    with st.spinner("Shruti is checking the desk..."):
        answer, route = send_to_shruti(content)
    if answer is not None:
        st.session_state.messages.append({"role": "assistant", "content": answer, "route": route})
    st.session_state.pending_transcript = None
    st.session_state.pending_audio = None
    st.session_state.widget_key += 1
    st.rerun()


health = api_health()

with st.sidebar:
    st.markdown("### Shruti")
    st.caption("Voice concierge")
    if health is None:
        st.markdown("<p class='status-off'>Desk offline</p>", unsafe_allow_html=True)
    else:
        voice = "Nepali voice ready" if health.get("asr_loaded") else "Voice model not loaded"
        st.markdown(f"<p class='status-ok'>Desk open · {voice}</p>", unsafe_allow_html=True)

    if st.button("New conversation", type="primary", use_container_width=True):
        start_new_conversation()
        st.rerun()

    st.markdown("---")
    st.caption("CONVERSATIONS")
    threads = fetch_threads()
    if not threads:
        st.caption("Nothing saved yet.")

    for thread in threads:
        thread_id = thread["thread_id"]
        active = thread_id == st.session_state.thread_id
        label = (thread.get("title") or "New conversation").strip()
        if st.session_state.confirm_delete == thread_id:
            st.caption(f"Delete “{label}”?")
            yes_col, no_col = st.columns(2)
            with yes_col:
                if st.button("Delete", key=f"confirm_{thread_id}", use_container_width=True):
                    if delete_thread(thread_id) and active:
                        start_new_conversation()
                    st.session_state.confirm_delete = None
                    st.rerun()
            with no_col:
                if st.button("Keep", key=f"cancel_{thread_id}", use_container_width=True):
                    st.session_state.confirm_delete = None
                    st.rerun()
        else:
            row_col, del_col = st.columns([5, 1])
            with row_col:
                prefix = "● " if active else ""
                if st.button(prefix + label, key=f"thread_{thread_id}", use_container_width=True):
                    load_thread(thread_id)
                    st.rerun()
            with del_col:
                if st.button("×", key=f"del_{thread_id}"):
                    st.session_state.confirm_delete = thread_id
                    st.rerun()

    st.markdown("---")
    st.caption("HOLDS AT THE DESK")
    reservations = fetch_reservations()
    if not reservations:
        st.caption("No rooms held yet.")
    for stay in reservations[:6]:
        st.markdown(
            f"**{stay['name']}**  \n{stay['room_type']} · {stay['check_in']} → {stay['check_out']}"
        )

    st.markdown("---")
    st.caption("Speak Nepali, or type in either language. Replies stay as text.")


if not st.session_state.messages and not st.session_state.pending_transcript:
    st.markdown(
        """
        <div class="hero-kicker">Voice concierge</div>
        <div class="hero-title">Good day.<br>I’m Shruti.</div>
        <p class="hero-copy">
        Ask about the stay, or hold a room.
        Speak Nepali if you prefer — I’ll transcribe it before I answer.
        </p>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    if health is None:
        st.markdown(
            "<div class='offline-note'>The desk API is not running, so these prompts cannot be answered yet.</div>",
            unsafe_allow_html=True,
        )
    left, right = st.columns(2)
    for index, (label, prompt_text) in enumerate(SUGGESTIONS):
        column = left if index % 2 == 0 else right
        with column:
            if st.button(label, key=f"suggest_{index}", use_container_width=True):
                send_message(prompt_text)

for message in st.session_state.messages:
    avatar = "🌿" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.write(message["content"])
        if message["role"] == "user" and message.get("audio"):
            st.audio(message["audio"])
        route = message.get("route")
        if message["role"] == "assistant" and route:
            st.markdown(
                f"<span class='pill'>{ROUTE_LABELS.get(route, route)}</span>",
                unsafe_allow_html=True,
            )

if st.session_state.pending_transcript:
    st.markdown("##### Check the transcript")
    st.caption("This came from the Nepali speech model. Edit it if a word is off, then send.")
    draft = st.text_area(
        "Transcript",
        value=st.session_state.pending_transcript,
        label_visibility="collapsed",
        key=f"draft_{st.session_state.widget_key}",
    )
    if st.session_state.pending_audio:
        st.audio(st.session_state.pending_audio)
    send_col, discard_col = st.columns(2)
    with send_col:
        if st.button("Send to Shruti", type="primary", use_container_width=True):
            send_message(draft, st.session_state.pending_audio)
    with discard_col:
        if st.button("Discard", use_container_width=True):
            st.session_state.pending_transcript = None
            st.session_state.pending_audio = None
            st.session_state.widget_key += 1
            st.rerun()

voice_col, type_col = st.columns([1.15, 5], vertical_alignment="bottom")
with voice_col:
    with st.popover("Speak Nepali", use_container_width=True):
        st.caption("Record a short message. You can correct the transcript before it is sent.")
        recorded = st.audio_input(
            "Record",
            key=f"mic_{st.session_state.widget_key}",
            label_visibility="collapsed",
        )
        if recorded is not None and st.session_state.pending_transcript is None:
            with st.spinner("Transcribing..."):
                transcript = transcribe_only(recorded.getvalue())
            if transcript:
                st.session_state.pending_transcript = transcript
                st.session_state.pending_audio = recorded.getvalue()
                st.rerun()
            elif transcript == "":
                st.warning("No speech in that clip. Try again a little closer to the mic.")
with type_col:
    prompt = st.chat_input("Message Shruti...")
    if prompt:
        send_message(prompt)
