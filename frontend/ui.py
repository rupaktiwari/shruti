import uuid

import requests
import streamlit as st

# API_URL = "http://127.0.0.1:8000"
API_URL = "https://wandererupak-shruti.hf.space"

st.set_page_config(page_title="Shruti", page_icon="🎙️")

st.markdown(
    """
    <style>
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #2563EB;
        color: white;
        border: 1px solid #2563EB;
    }
    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background-color: #1D4ED8;
        color: white;
        border: 1px solid #1D4ED8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

defaults = {
    "messages": [],
    "thread_id": f"v1-{uuid.uuid4().hex}",
    "pending_transcript": None,
    "pending_audio": None,
    "widget_key": 0,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


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


def synthesize_speech(text):
    text = text.strip()
    if not text:
        return None
    response = requests.post(f"{API_URL}/tts", json={"text": text}, timeout=300)
    if response.status_code != 200 or not response.content:
        st.error(f"TTS failed: {response.text}")
        return None
    return response.content


# ------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------
with st.sidebar:
    st.title("🎙️ Shruti")

    if st.button("➕ New Conversation", type="primary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = f"v1-{uuid.uuid4().hex}"
        st.session_state.pending_transcript = None
        st.session_state.pending_audio = None
        st.session_state.widget_key += 1
        st.rerun()

    st.markdown("---")
    st.caption("Past conversations")

    try:
        threads = requests.get(f"{API_URL}/conversations", timeout=10).json()
    except requests.exceptions.RequestException:
        threads = []

    if not threads:
        st.caption("_No conversations yet_")

    for thread in threads:
        is_active = thread["thread_id"] == st.session_state.thread_id
        label = ("👉 " if is_active else "💬 ") + (thread["title"] or "(empty)")
        if st.button(label, key=f"thread_{thread['thread_id']}", use_container_width=True):
            st.session_state.thread_id = thread["thread_id"]
            history = requests.get(f"{API_URL}/conversations/{thread['thread_id']}", timeout=10).json()
            # Note: past audio recordings aren't stored, only text —
            # reloaded messages show text/route but no playback of the
            # original user recording.
            st.session_state.messages = [
                {"role": m["role"], "content": m["content"], "route": m.get("route"), "audio": None}
                for m in history
            ]
            st.session_state.pending_transcript = None
            st.session_state.pending_audio = None
            st.rerun()

    st.markdown("---")

    st.markdown("---")
    st.caption("V2 is an experimental streaming ASR --- ongoing project. It's behaviour is erratic as of now.")


# ------------------------------------------------------------------
# CHAT HISTORY
# ------------------------------------------------------------------
st.write("An End-to-End Nepali Speech Recognition and Conversational Agent")

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.write(message["content"])

        if message["role"] == "user" and message.get("audio"):
            st.audio(message["audio"])

        if message["role"] == "assistant":
            st.caption(f"Route: `{message.get('route', '')}`")
            if message.get("audio"):
                st.audio(message["audio"], format="audio/wav")
            elif st.button("🔊 Speak this response", key=f"speak_{i}"):
                with st.spinner("Generating speech..."):
                    audio = synthesize_speech(message["content"])
                if audio:
                    st.session_state.messages[i]["audio"] = audio
                    st.rerun()


# ------------------------------------------------------------------
# INPUT AREA
# ------------------------------------------------------------------
st.markdown("---")

recorded_audio = st.audio_input("🎤 Record your message", key=f"mic_{st.session_state.widget_key}")

if recorded_audio and st.session_state.pending_transcript is None:
    with st.spinner("Transcribing..."):
        audio_bytes = recorded_audio.getvalue()
        transcript = transcribe_only(audio_bytes, "wav")
    if transcript:
        st.session_state.pending_transcript = transcript
        st.session_state.pending_audio = audio_bytes
        st.rerun()
    elif transcript == "":
        st.warning("🔇 No speech detected. Try again.")

if st.session_state.pending_transcript:
    st.markdown("**Transcript preview** (hover for copy icon):")
    st.code(st.session_state.pending_transcript, language="text")

    col_send, col_discard = st.columns([1, 1])
    with col_send:
        if st.button("➤ Send", type="secondary", use_container_width=True):
            transcript = st.session_state.pending_transcript
            audio = st.session_state.pending_audio

            st.session_state.messages.append({"role": "user", "content": transcript, "audio": audio})

            with st.spinner("Shruti is responding..."):
                answer, route = send_to_shruti(transcript)

            if answer is not None:
                st.session_state.messages.append({"role": "assistant", "content": answer, "route": route, "audio": None})

            st.session_state.pending_transcript = None
            st.session_state.pending_audio = None
            st.session_state.widget_key += 1
            st.rerun()

    with col_discard:
        if st.button("🗑️ Discard", type="primary", use_container_width=True):
            st.session_state.pending_transcript = None
            st.session_state.pending_audio = None
            st.session_state.widget_key += 1
            st.rerun()