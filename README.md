# 🎙️ Project Shruti: End-to-End Nepali Speech Recognition

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Hugging Face](https://img.shields.io/badge/%F0%9F%A4%97_Hugging_Face-Spaces-yellow?style=for-the-badge)

## 📖 About the Project

**Shruti** is a fully containerized, locally quantized Automatic Speech Recognition (ASR) application designed exclusively for the Nepali language. 

Currently, robust speech-to-text solutions for low-resource languages like Nepali are often locked behind expensive, cloud-dependent APIs. Project Shruti was built to solve this by bringing powerful, accurate Nepali transcription entirely **offline** and making it accessible on standard consumer hardware.

By taking a massive, resource-heavy **Wav2Vec2-BERT** model and mathematically quantizing its weights (reducing it to an ~834 MB `.pt` file), this application drastically reduces the memory footprint required for inference. The result is a highly accurate AI brain that runs blazingly fast on **CPU-only environments**, wrapped in a robust FastAPI backend and paired with a seamless Streamlit user interface.

**Key Highlights:**
* **100% Free Inference:** No API keys, no paywalls, and no reliance on third-party cloud servers like OpenAI or Google Cloud.
* **Hardware Optimized:** Quantized to run efficiently on standard CPUs without requiring expensive NVIDIA GPUs.
* **Continuous Deployment (CD):** Decoupled architecture where the frontend UI updates in real-time upon GitHub pushes, while the heavy backend remains stably hosted on Hugging Face Spaces.

---

## 🚀 Live Demo & Links

* **Frontend UI (Streamlit):** [https://shruti.streamlit.app/](https://shruti.streamlit.app/)
* **Backend (Fast API hosted on Hugging Face Spaces):** [https://wandererupak-shruti.hf.space/docs](https://wandererupak-shruti.hf.space/docs)
* **Docker Image:** [wandererupak/shruti:v1 on Docker Hub](https://hub.docker.com/r/wandererupak/shruti/tags)

---

## 🧠 Architecture & Tech Stack



* **Machine Learning Model:** Locally quantized Wav2Vec2-BERT trained on OSLR 54 Nepali Speech Dataset using (PyTorch, Torchaudio, Transformers).
* **Backend:** FastAPI running on Uvicorn, serving endpoints on Port 7860.
* **Frontend:** Streamlit, decoupled and communicating with the backend via REST API.
* **Package Management:** `uv` (Lightning-fast Python package manager).
* **Containerization:** Docker (`Dockerfile` included for multi-stage builds).
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

Built with ❤️ by [Rupak Tiwari](https://www.linkedin.com/in/rupak-tiwari-719ba626a) with the help of ChatGPT and Gemini.

