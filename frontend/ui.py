import uuid

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"
# API_URL = "https://wandererupak-shruti.hf.space"

st.set_page_config(page_title="Shruti", page_icon="🎙️", layout="wide")

# ------------------------------------------------------------------
# PREMIUM THEME
# ------------------------------------------------------------------
st.markdown(
    """
    <style>
    .main .block-container {
        max-width: 760px;
        padding-top: 2rem;
        padding-bottom: 7rem;
        margin: 0 auto;
    }

    section[data-testid="stSidebar"] {
        background-color: #171717;
        border-right: 1px solid #2a2a2a;
    }
    section[data-testid="stSidebar"] * {
        color: #e8e8e6 !important;
    }
    section[data-testid="stSidebar"] button {
        background-color: transparent !important;
        border: 1px solid #3a3a3a !important;
        text-align: left !important;
        justify-content: flex-start !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background-color: #2a2a2a !important;
    }

    div[data-testid="stChatMessage"] {
        padding: 0.6rem 0.9rem;
        border-radius: 16px;
        margin-bottom: 0.4rem;
    }

    div[data-testid="stChatInput"] textarea {
        border-radius: 999px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------------
# STATE
# ------------------------------------------------------------------
defaults = {
    "messages": [],
    "thread_id": f"v1-{uuid.uuid4().hex}",
    "pending_transcript": None,
    "pending_audio": None,
    "widget_key": 0,
    "confirm_delete": None,
}
for key, value in defaults.items():
    st.session_state.setdefault(key, value)


# ------------------------------------------------------------------
# API HELPERS
# ------------------------------------------------------------------
def transcribe_only(audio_bytes, file_type):
    files = {"file": (f"audio.{file_type}", audio_bytes, f"audio/{file_type}")}
    response = requests.post(f"{API_URL}/transcribe", files=files, timeout=300)
    if response.status_code != 200:
        st.error(f"Transcription failed: {response.text}")
        return None
    return response.json().get("transcription", "").strip()


def send_to_shruti(transcript):
    response = requests.post(
        f"{API_URL}/converse",
        json={"transcript": transcript, "thread_id": st.session_state.thread_id},
        timeout=300,
    )
    if response.status_code != 200:
        st.error(f"Conversation failed: {response.text}")
        return None, None
    result = response.json()
    return result.get("answer", ""), result.get("route", "")


def fetch_threads():
    try:
        return requests.get(f"{API_URL}/conversations", timeout=10).json()
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
    st.session_state.thread_id = f"v1-{uuid.uuid4().hex}"
    st.session_state.pending_transcript = None
    st.session_state.pending_audio = None
    st.session_state.widget_key += 1


def load_thread(thread_id):
    st.session_state.thread_id = thread_id
    history = requests.get(f"{API_URL}/conversations/{thread_id}", timeout=10).json()
    st.session_state.messages = [
        {"role": m["role"], "content": m["content"], "route": m.get("route"), "audio": None}
        for m in history
    ]
    st.session_state.pending_transcript = None
    st.session_state.pending_audio = None


def send_message(content, audio=None):
    st.session_state.messages.append({"role": "user", "content": content, "audio": audio})
    with st.spinner("Shruti is thinking..."):
        answer, route = send_to_shruti(content)
    if answer is not None:
        st.session_state.messages.append({"role": "assistant", "content": answer, "route": route})
    st.session_state.pending_transcript = None
    st.session_state.pending_audio = None
    st.session_state.widget_key += 1
    st.rerun()


# ------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎙️ Shruti")
    st.caption("Nepali speech & conversational agent")

    if st.button("➕  New chat", type="primary", use_container_width=True):
        start_new_conversation()
        st.rerun()

    st.markdown("---")
    st.caption("CONVERSATIONS")

    threads = fetch_threads()
    if not threads:
        st.caption("_No conversations yet_")

    for thread in threads:
        tid = thread["thread_id"]
        is_active = tid == st.session_state.thread_id
        label = thread["title"] or "New conversation"

        if st.session_state.confirm_delete == tid:
            st.caption(f"Delete “{label}”? This can't be undone.")
            confirm_col, cancel_col = st.columns(2)
            with confirm_col:
                if st.button("Delete", key=f"confirm_{tid}", use_container_width=True):
                    if delete_thread(tid) and is_active:
                        start_new_conversation()
                    st.session_state.confirm_delete = None
                    st.rerun()
            with cancel_col:
                if st.button("Cancel", key=f"cancel_{tid}", use_container_width=True):
                    st.session_state.confirm_delete = None
                    st.rerun()
        else:
            row_col, del_col = st.columns([5, 1])
            with row_col:
                btn_label = ("👉 " if is_active else "💬 ") + label
                if st.button(btn_label, key=f"thread_{tid}", use_container_width=True):
                    load_thread(tid)
                    st.rerun()
            with del_col:
                if st.button("🗑️", key=f"del_{tid}"):
                    st.session_state.confirm_delete = tid
                    st.rerun()

    st.markdown("---")
    st.caption(
        "🧪 Shruti V2 is an experimental streaming-ASR build — "
        "see it on the **Shruti V2** page in the sidebar above. "
        "Erratic behaviour expected; not part of this build."
    )


# ------------------------------------------------------------------
# CHAT HISTORY
# ------------------------------------------------------------------
if not st.session_state.messages and not st.session_state.pending_transcript:
    st.markdown(
        "<div style='text-align:center; margin-top:15vh; opacity:0.6;'>"
        "<h2>🎙️ Shruti</h2>"
        "<p>Ask anything — type below, or record a voice message.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

for message in st.session_state.messages:
    avatar = "🧑" if message["role"] == "user" else "🎙️"
    with st.chat_message(message["role"], avatar=avatar):
        st.write(message["content"])
        if message["role"] == "user" and message.get("audio"):
            st.audio(message["audio"])
        if message["role"] == "assistant" and message.get("route"):
            st.caption(f"Route: `{message['route']}`")

if st.session_state.pending_transcript:
    with st.chat_message("user", avatar="🧑"):
        st.write(st.session_state.pending_transcript)
        st.caption("🎤 Transcribed from voice — review before sending")

    send_col, discard_col = st.columns(2)
    with send_col:
        if st.button("➤ Send", type="primary", use_container_width=True, key="send_voice"):
            send_message(st.session_state.pending_transcript, st.session_state.pending_audio)
    with discard_col:
        if st.button("Discard", use_container_width=True, key="discard_voice"):
            st.session_state.pending_transcript = None
            st.session_state.pending_audio = None
            st.session_state.widget_key += 1
            st.rerun()


# ------------------------------------------------------------------
# INPUT AREA — text is primary, voice is an optional extra
# ------------------------------------------------------------------
with st.popover("🎤 Voice message"):
    st.caption("Record instead of typing — works best in Nepali")
    recorded_audio = st.audio_input(
        "Record", key=f"mic_{st.session_state.widget_key}", label_visibility="collapsed"
    )
    if recorded_audio and st.session_state.pending_transcript is None:
        with st.spinner("Transcribing..."):
            transcript = transcribe_only(recorded_audio.getvalue(), "wav")
        if transcript:
            st.session_state.pending_transcript = transcript
            st.session_state.pending_audio = recorded_audio.getvalue()
            st.rerun()
        elif transcript == "":
            st.warning("🔇 No speech detected. Try again.")

text_prompt = st.chat_input("Message Shruti...")
if text_prompt:
    send_message(text_prompt)