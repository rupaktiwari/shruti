import streamlit as st
import requests
import time
import threading
from streamlit.runtime.scriptrunner import add_script_run_ctx

# ------------------------------------------------------------------
# 🔗 CONFIGURATION (LOCAL MODE)
# ------------------------------------------------------------------
# API_URL = "http://127.0.0.1:8000"  # Pointing to your own machine
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# 🔗 CONFIGURATION (CLOUD MODE)
# ------------------------------------------------------------------
API_URL = "https://wandererupak-shruti.hf.space"


st.set_page_config(page_title="Project Shruti", page_icon="🎙️")

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
    st.session_state.last_audio = None  # NEW: Remember the audio file

st.title("🎙️ Shruti")
st.write("An End-to-End Nepali Speech Recognition Tool")

# Helper function to send audio to FastAPI and run the live timer
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
            st.session_state.last_audio = audio_file  # NEW: Save the audio to memory
            
            st.rerun() 
        else:
            st.error(f"Error {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        stop_event.set()
        timer_placeholder.empty()
        st.error(f"❌ Could not connect to {API_URL}. Is 'uv run fastapi dev app/main.py' running?")


# ==========================================
# 🖥️ USER INTERFACE RENDERING
# ==========================================

# SCENARIO A: No transcription yet -> Show the Upload/Record Tabs
if st.session_state.result_text is None:
    tab1, tab2 = st.tabs(["🎤 Record Audio", "📂 Upload File"])

    with tab1:
        audio_bytes = st.audio_input("Click to record", key=f"mic_{st.session_state.widget_key}")
        if audio_bytes:
            st.audio(audio_bytes)
            if st.button("Transcribe Recording", type="primary"):
                transcribe_audio(audio_bytes, "wav")

    with tab2:
        uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "webm"], key=f"upload_{st.session_state.widget_key}")
        if uploaded_file:
            st.audio(uploaded_file)
            if st.button("Transcribe File", type="primary"):
                ext = uploaded_file.name.split(".")[-1]
                transcribe_audio(uploaded_file, ext)

# SCENARIO B: Transcription is done -> Show Results & Clear Button
else:
    st.success(f"✅ Transcription Complete! (Took {st.session_state.time_taken} seconds)")
    
    # NEW: Display the saved audio player right above the text
    if st.session_state.last_audio:
        st.audio(st.session_state.last_audio)
    
    st.markdown(f"### 📝 Output:\n**{st.session_state.result_text}**")
    
    with st.expander("🔍 Model Details"):
        st.write(f"Model Used: {st.session_state.model_details}")
        
    st.markdown("---")
    
    # THE CLEAR BUTTON
    if st.button("🔄 Clear & Transcribe Another", type="primary"):
        st.session_state.result_text = None
        st.session_state.model_details = None
        st.session_state.time_taken = None
        st.session_state.last_audio = None  # NEW: Clear the audio from memory
        st.session_state.widget_key += 1 
        st.rerun()