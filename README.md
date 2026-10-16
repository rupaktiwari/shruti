---
title: Shruti
emoji: 🌍
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# 🎙️ Project Shruti: End-to-End Nepali Speech Recognition and Conversational AI Assistant

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97_Hugging_Face-Spaces-yellow?style=for-the-badge)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)

## 📖 About the Project

**Shruti** is a fully containerized, locally quantized Automatic Speech Recognition (ASR) and conversational AI agent built for the Nepali language — combining a self-trained ASR model with an agentic RAG assistant that routes between retrieval, general LLM responses, and human escalation.

Currently, robust speech-to-text solutions for low-resource languages like Nepali are often locked behind expensive, cloud-dependent APIs. Project Shruti was built to solve this by bringing powerful, accurate Nepali transcription entirely offline and making it accessible on standard consumer hardware.

By taking a massive, resource-heavy Wav2Vec2-BERT model and mathematically quantizing its weights (reducing it to an ~834 MB `.pt` file), this application drastically reduces the memory footprint required for inference. The result is a highly accurate AI brain that runs blazingly fast on CPU-only environments, wrapped in a robust FastAPI backend and paired with a ChatGPT-style Streamlit interface.

**Key Highlights of Work Done**
* Fine-tuned Wav2Vec2-BERT on OSLR 54 Nepali speech data, tracking convergence with Weights & Biases over 136 GPU hours.

* Engineered a decoupled, quantized (FP32 -> INT8) inference pipeline with VAD for silence/noise filtering and reliable transcription.

* Designed intent routing across RAG, general responses, and human escalation, with ChromaDB RAG using sentence-transformer embeddings and a custom knowledge base.

* Implemented SQLite-backed persistent, multi-turn conversation state, including full create/read/delete conversation management.

* Rebuilt the frontend as a single-page, ChatGPT-style chat interface — text-first querying with voice input as an optional secondary mode, replacing the earlier batch record/upload flow.

* Exposed ASR and conversational workflows via FastAPI with a Streamlit frontend.

* Containerized the backend with Docker and automated deployment to Hugging Face Spaces via a GitHub Actions CI/CD pipeline, removing the need for manual Docker builds on every change.

* Prototyped real-time streaming ASR using WebSockets, VADIterator, and streamlit-webrtc; kept as a separate, clearly labeled experimental page (Shruti V2) rather than part of the main product, due to transcription quality issues under streaming.

---

## 🚀 Live Demo & Links

* **Frontend UI (Streamlit):** [https://shruti.streamlit.app/](https://shruti.streamlit.app/)
* **Backend (FastAPI hosted on Hugging Face Spaces):** [https://wandererupak-shruti.hf.space/docs](https://wandererupak-shruti.hf.space/docs)
* **Docker Image:** [wandererupak/shruti:latest on Docker Hub](https://hub.docker.com/r/wandererupak/shruti/tags)

---

## 🧠 Architecture & Tech Stack

* **Machine Learning Model:** Locally quantized Wav2Vec2-BERT trained on OSLR 54 Nepali Speech Dataset using (PyTorch, Torchaudio, Transformers).
* **Orchestration:** LangGraph-based agent with intent routing (RAG / general LLM / human escalation) and per-thread conversation memory.
* **Backend:** FastAPI running on Uvicorn, serving endpoints on Port 7860.
* **Frontend:** Streamlit, decoupled and communicating with the backend via REST API; ChatGPT-style chat UI with persistent, deletable multi-turn conversations.
* **Package Management:** `uv` (Lightning-fast Python package manager).
* **Containerization:** Docker (`Dockerfile` included for multi-stage builds).
* **CI/CD:** GitHub Actions automatically deploys to the Hugging Face Space on every push to `main`.
* **Cloud Infrastructure:** Hugging Face Spaces (Backend) & Streamlit Community Cloud (Frontend).

---

🧠 **[Quantized Shruti Model](https://drive.google.com/drive/folders/1IedTP-uHqRpqblbGjzuBf1rEe60D9HQ1?usp=sharing)**: Just in case you wish to run the app locally, you need to have the folder inside the drive link in your project directory.

---

## 🐳 Running with Docker (Recommended)

You do not need to clone this repository or manually download the heavy ML model to run the application. The entire environment, Python dependencies, and the quantized AI model are pre-packaged into a Docker image.

Run the backend API instantly with one command:

```bash
docker run -p 7860:7860 wandererupak/shruti:v1
```

---
