import streamlit as st
import requests
import time
import threading
import uuid
import json
import numpy as np
import librosa
import websocket  # from websocket-client
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# ------------------------------------------------------------------
# 🔗 CONFIGURATION (LOCAL MODE)
# ------------------------------------------------------------------
API_URL = "https://wandererupak-shruti.hf.space"# ------------------------------------------------------------------
# 🔗 CONFIGURATION (CLOUD MODE)
# ------------------------------------------------------------------
# API_URL = "https://wandererupak-shruti.hf.space"


st.set_page_config(page_title="Shruti", page_icon="🎙️")

# Style "Send to Shruti" (type="secondary") buttons in blue —
# type="primary" buttons (Transcribe Recording/File) are untouched.
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

# --- INITIALIZE SESSION STATE ---
if "result_text" not in st.session_state:
    st.session_state.result_text = None
if "model_details" not in st.session_state:
    st.session_state.model_details = None
if "time_taken" not in st.session_state:
    st.session_state.time_taken = None
if "widget_key" not in st.session_state:
    st.session_state.widget_key = 0
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None
if "conversation_answer" not in st.session_state:
    st.session_state.conversation_answer = None
if "conversation_route" not in st.session_state:
    st.session_state.conversation_route = None
if "v1_thread_id" not in st.session_state:
    st.session_state.v1_thread_id = f"v1-{uuid.uuid4().hex}"

st.title("🎙️ Shruti")
st.write("An End-to-End Nepali Speech Recognition and Conversational System")


def transcribe_audio(audio_file, file_type):
    """Transcribe only — no orchestration, no LLM call."""
    timer_placeholder = st.empty()
    stop_event = threading.Event()

    def run_timer():
        start_time = time.time()
        while not stop_event.is_set():
            elapsed = int(time.time() - start_time)
            timer_placeholder.info(f"⏳ **Processing Audio...** {elapsed} seconds elapsed")
            time.sleep(0.5)

    timer_thread = threading.Thread(target=run_timer)
    add_script_run_ctx(timer_thread)
    timer_thread.start()

    start_time_exact = time.time()
    try:
        files = {"file": (f"audio.{file_type}", audio_file, f"audio/{file_type}")}
        response = requests.post(f"{API_URL}/transcribe", files=files)

        stop_event.set()
        timer_thread.join()
        timer_placeholder.empty()

        total_time = round(time.time() - start_time_exact, 2)

        if response.status_code == 200:
            result = response.json()
            st.session_state.result_text = result.get("transcription", "Error: Key not found")
            st.session_state.model_details = result.get("model_used")
            st.session_state.time_taken = total_time
            st.session_state.last_audio = audio_file
            st.session_state.conversation_answer = None
            st.session_state.conversation_route = None
            st.rerun()
        else:
            st.error(f"Error {response.status_code}: {response.text}")

    except requests.exceptions.ConnectionError:
        stop_event.set()
        timer_placeholder.empty()
        st.error(f"❌ Could not connect to {API_URL}. Is 'uv run fastapi dev app/main.py' running?")


def send_audio_to_shruti(audio_file, file_type):
    """Transcribe AND send to the LangGraph orchestrator for a response."""
    progress_placeholder = st.empty()
    progress_placeholder.info("🎧 Shruti is hearing...")

    start_time_exact = time.time()
    try:
        audio_bytes = audio_file.getvalue() if hasattr(audio_file, "getvalue") else audio_file
        files = {"file": (f"audio.{file_type}", audio_bytes, f"audio/{file_type}")}

        transcription_response = requests.post(f"{API_URL}/transcribe", files=files, timeout=300)

        if transcription_response.status_code != 200:
            progress_placeholder.error(f"Transcription failed: {transcription_response.text}")
            return

        transcription_result = transcription_response.json()
        transcript = transcription_result.get("transcription", "").strip()

        st.session_state.result_text = transcript
        st.session_state.model_details = transcription_result.get("model_used")
        st.session_state.last_audio = audio_bytes

        if not transcript:
            st.session_state.time_taken = round(time.time() - start_time_exact, 2)
            st.session_state.conversation_answer = None
            st.session_state.conversation_route = None
            st.rerun()
            return

        progress_placeholder.info("🤔 Shruti is responding...")

        conversation_response = requests.post(
            f"{API_URL}/converse",
            json={"transcript": transcript, "thread_id": st.session_state.v1_thread_id},
            timeout=300,
        )

        if conversation_response.status_code != 200:
            progress_placeholder.error(f"Conversation failed: {conversation_response.text}")
            return

        conversation_result = conversation_response.json()
        st.session_state.conversation_answer = conversation_result.get("answer", "")
        st.session_state.conversation_route = conversation_result.get("route", "")
        st.session_state.time_taken = round(time.time() - start_time_exact, 2)

        st.rerun()

    except requests.exceptions.ConnectionError:
        progress_placeholder.error(f"Could not connect to {API_URL}. Is FastAPI running?")
    except requests.exceptions.RequestException as error:
        progress_placeholder.error(f"Request failed: {error}")


# ==========================================
# 🖥️ TOP-LEVEL SECTIONS
# ==========================================
v1_tab, v2_tab = st.tabs(["📝 Shruti V1 — Conversational Agent", "🗣️ Shruti V2 — Streaming (Experimental)"])

# ------------------------------------------------------------------
# SHRUTI V1
# ------------------------------------------------------------------
with v1_tab:
    st.caption(
        "End-to-end voice assistant. Record or upload audio, then choose: "
        "'Transcribe Only' for a plain transcript, or 'Send to Shruti' to also "
        "get a response back. Currently, Shruti can answer both in-domain queries (E-sewa KYC for prototype) using "
        "RAG and out-of-domain queries using only an LLM. It can also escalate — generate a response that triggers "
        "human in the loop. Currently the medium to involve humans is not set so it plainly responds in text."
    )

    if st.session_state.result_text is None:
        tab1, tab2 = st.tabs(["🎤 Record Audio", "📂 Upload File"])

        with tab1:
            audio_bytes = st.audio_input("Click to record", key=f"mic_{st.session_state.widget_key}")
            if audio_bytes:
                st.audio(audio_bytes)
                col1, _, col2 = st.columns([1, 3, 1])
                with col1:
                    if st.button("Transcribe Recording", type="primary", key="v1_transcribe_recording"):
                        transcribe_audio(audio_bytes, "wav")
                with col2:
                    if st.button("Send to Shruti", type="secondary", key="v1_send_recording"):
                        send_audio_to_shruti(audio_bytes, "wav")

        with tab2:
            uploaded_file = st.file_uploader(
                "Upload an audio file", type=["wav", "mp3", "webm"], key=f"upload_{st.session_state.widget_key}"
            )
            if uploaded_file:
                st.audio(uploaded_file)
                ext = uploaded_file.name.split(".")[-1].lower()
                col1, _, col2 = st.columns([1, 3, 1])
                with col1:
                    if st.button("Transcribe File", type="primary", key="v1_transcribe_file"):
                        transcribe_audio(uploaded_file, ext)
                with col2:
                    if st.button("Send to Shruti", type="secondary", key="v1_send_file"):
                        send_audio_to_shruti(uploaded_file, ext)

    else:
        if st.session_state.result_text == "":
            st.warning("🔇 No speech detected in the recording. Please try again.")
            if st.session_state.last_audio:
                st.audio(st.session_state.last_audio)
        else:
            st.success(f"✅ Transcription Complete! (Took {st.session_state.time_taken} seconds)")
            if st.session_state.last_audio:
                st.audio(st.session_state.last_audio)

            st.markdown("### 📝 Output:")
            st.code(st.session_state.result_text, language="text")

            with st.expander("🔍 Model Details"):
                st.write(f"Model Used: {st.session_state.model_details}")

            if st.session_state.conversation_answer:
                st.markdown("### 🤖 Shruti's Response")
                st.write(st.session_state.conversation_answer)
                st.caption(f"LangGraph route: `{st.session_state.conversation_route}`")

        st.markdown("---")
        if st.button("🔄 Clear", type="primary"):
            st.session_state.result_text = None
            st.session_state.model_details = None
            st.session_state.time_taken = None
            st.session_state.last_audio = None
            st.session_state.conversation_answer = None
            st.session_state.conversation_route = None
            st.session_state.v1_thread_id = f"v1-{uuid.uuid4().hex}"
            st.session_state.widget_key += 1
            st.rerun()

# ------------------------------------------------------------------
# SHRUTI V2 (EXPERIMENTAL — TRANSCRIPTION ONLY)
# ------------------------------------------------------------------
with v2_tab:
    st.caption(
        "Experimental streaming ASR. Speak naturally and pause to receive "
        "a live transcript. This version currently performs transcription only; "
        "it does not yet send the transcript to LangGraph or provide TTS."
    )

    webrtc_ctx = webrtc_streamer(
        key="shruti-v2-mic",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=256,
        media_stream_constraints={"audio": True, "video": False},
    )

    status_placeholder = st.empty()
    transcript_placeholder = st.empty()
    debug_placeholder = st.empty()

    if webrtc_ctx.state.playing:
        status_placeholder.info("🎙️ Listening... speak naturally, pause when you're done. Click Stop when finished.")

        ws_url = "ws://127.0.0.1:8000/ws/transcribe"
        ws_conn = websocket.create_connection(ws_url)
        debug_shown = False

        try:
            while webrtc_ctx.state.playing:
                if webrtc_ctx.audio_receiver:
                    try:
                        audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
                    except Exception:
                        audio_frames = []

                    for frame in audio_frames:
                        audio_array = frame.to_ndarray()

                        if not debug_shown:
                            debug_placeholder.write(
                                f"Frame debug — shape: {audio_array.shape}, "
                                f"dtype: {audio_array.dtype}, "
                                f"native rate: {frame.sample_rate}"
                            )
                            debug_shown = True

                        audio_mono = audio_array.astype(np.float32).flatten() / 32768.0
                        resampled = librosa.resample(audio_mono, orig_sr=frame.sample_rate, target_sr=16000)
                        pcm_bytes = (resampled * 32768.0).astype(np.int16).tobytes()

                        ws_conn.send_binary(pcm_bytes)

                    ws_conn.settimeout(0.05)
                    try:
                        response = ws_conn.recv()
                        result = json.loads(response)
                        transcript_placeholder.success(f"📝 {result['text']}")
                    except Exception:
                        pass
        finally:
            ws_conn.close()
    else:
        status_placeholder.empty()