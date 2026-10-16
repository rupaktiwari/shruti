import json

import librosa
import numpy as np
import streamlit as st
import websocket
from streamlit_webrtc import WebRtcMode, webrtc_streamer

st.set_page_config(page_title="V2 (Experimental)", page_icon="🗣️")

st.title("🗣️ Shruti V2 — Streaming (Experimental)")
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
    status_placeholder.info(
        "🎙️ Listening... speak naturally, pause when you're done. "
        "Click Stop when finished."
    )

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