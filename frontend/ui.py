import streamlit as st
import requests
import time
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit_webrtc import webrtc_streamer, WebRtcMode

# ------------------------------------------------------------------
# 🔗 CONFIGURATION (LOCAL MODE)
# ------------------------------------------------------------------
API_URL = "http://127.0.0.1:8000"
# ------------------------------------------------------------------
# 🔗 CONFIGURATION (CLOUD MODE)
# ------------------------------------------------------------------
# API_URL = "https://wandererupak-shruti.hf.space"


st.set_page_config(page_title="Shruti", page_icon="🎙️")

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

st.title("🎙️ Shruti")
st.write("An End-to-End Nepali Speech Recognition and Conversational System")


def transcribe_audio(audio_file, file_type):
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
            st.rerun()
        else:
            st.error(f"Error {response.status_code}: {response.text}")

    except requests.exceptions.ConnectionError:
        stop_event.set()
        timer_placeholder.empty()
        st.error(f"❌ Could not connect to {API_URL}. Is 'uv run fastapi dev app/main.py' running?")


# ==========================================
# 🖥️ TOP-LEVEL SECTIONS
# ==========================================
v1_tab, v2_tab = st.tabs(["📝 Shruti V1 — Transcription", "🗣️ Shruti V2 — Conversational Agent"])

# ------------------------------------------------------------------
# SHRUTI V1
# ------------------------------------------------------------------
with v1_tab:
    st.caption(
        "Batch transcription. Record or upload a clip, get a clean transcript back — "
        "no conversation, no orchestration. Good for dictation, voice notes, and "
        "quick transcripts."
    )

    if st.session_state.result_text is None:
        tab1, tab2 = st.tabs(["🎤 Record Audio", "📂 Upload File"])

        with tab1:
            audio_bytes = st.audio_input("Click to record", key=f"mic_{st.session_state.widget_key}")
            if audio_bytes:
                st.audio(audio_bytes)
                if st.button("Transcribe Recording", type="primary"):
                    transcribe_audio(audio_bytes, "wav")

        with tab2:
            uploaded_file = st.file_uploader(
                "Upload an audio file", type=["wav", "mp3", "webm"], key=f"upload_{st.session_state.widget_key}"
            )
            if uploaded_file:
                st.audio(uploaded_file)
                if st.button("Transcribe File", type="primary"):
                    ext = uploaded_file.name.split(".")[-1]
                    transcribe_audio(uploaded_file, ext)

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

        st.markdown("---")
        if st.button("🔄 Clear & Transcribe Another", type="primary"):
            st.session_state.result_text = None
            st.session_state.model_details = None
            st.session_state.time_taken = None
            st.session_state.last_audio = None
            st.session_state.widget_key += 1
            st.rerun()

# ------------------------------------------------------------------
# SHRUTI V2
# ------------------------------------------------------------------
with v2_tab:
    st.caption(
        "Live conversation. Speak naturally with pauses — streaming VAD detects "
        "when you've finished a turn, a LangGraph agent decides how to respond, "
        "and TTS speaks back."
    )

    webrtc_ctx = webrtc_streamer(
        key="shruti-v2-mic",
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=256,
        media_stream_constraints={"audio": True, "video": False},
    )

    if webrtc_ctx.state.playing:
        st.write("🎙️ Mic connected — listening...")

        if webrtc_ctx.audio_receiver:
            try:
                audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
                st.write(f"Received {len(audio_frames)} audio frame(s) this cycle")
            except Exception:
                pass