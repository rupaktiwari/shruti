const SUGGESTIONS = [
  ["What Shruti can do", "What can you help me with, in a short answer?"],
  ["Plain-language RAG", "Explain retrieval-augmented generation in plain language."],
  ["A demo introduction", "Give me a three-line introduction I can use when I show this project."],
  ["Nepali greeting", "Write a short Nepali greeting I can use to open a demo."],
];

const state = {
  mode: "shruti",
  health: null,
  shrutiThreadId: id("shruti"),
  shrutiMessages: [],
  notebookId: null,
  notebooks: [],
  documents: [],
  smritiThreadId: null,
  smritiMessages: [],
  busy: false,
  recorder: null,
  reviewAudioUrl: null,
};

const $ = (selector) => document.querySelector(selector);

function id(prefix) {
  const hex = crypto.randomUUID().replaceAll("-", "").slice(0, 10);
  return prefix ? `${prefix}-${hex}` : hex;
}

function notice(text) {
  const node = $("#notice");
  node.hidden = !text;
  node.textContent = text || "";
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (response.ok) {
    if (response.status === 204) return null;
    const type = response.headers.get("content-type") || "";
    return type.includes("application/json") ? response.json() : null;
  }
  let detail = "The request failed.";
  try {
    const body = await response.json();
    detail = body.detail || detail;
    if (Array.isArray(detail)) detail = detail.map((item) => item.msg || String(item)).join(" ");
  } catch (_error) {
    detail = "The request failed.";
  }
  throw new Error(detail);
}

function setMode(mode) {
  state.mode = mode;
  const shruti = mode === "shruti";
  $("#mode-shruti").classList.toggle("is-active", shruti);
  $("#mode-smriti").classList.toggle("is-active", !shruti);
  $("#mode-shruti").setAttribute("aria-selected", String(shruti));
  $("#mode-smriti").setAttribute("aria-selected", String(!shruti));
  $("#shruti-nav").hidden = !shruti;
  $("#smriti-nav").hidden = shruti;
  $("#shruti-view").hidden = !shruti;
  $("#smriti-view").hidden = shruti;
  $("#message").placeholder = shruti ? "Message Shruti…" : "Ask Smriti about this notebook…";
  $("#review-send").textContent = shruti ? "Send to Shruti" : "Send to Smriti";
  $("#composer").hidden = !shruti && state.notebookId == null;
  discardReview();
  render();
}

function renderStatus() {
  const node = $("#status");
  if (!state.health) {
    node.textContent = "API offline";
    node.className = "status is-off";
    return;
  }
  const voice = state.health.asr_loaded ? "Nepali voice ready" : "Voice model not loaded";
  node.textContent = `Ready · ${voice}`;
  node.className = "status is-on";
}

function renderMessages(target, messages) {
  const log = $(target);
  log.replaceChildren();
  messages.forEach((message) => {
    const bubble = document.createElement("article");
    bubble.className = `bubble ${message.role}`;
    bubble.textContent = message.content;
    const names = [];
    (message.citations || []).forEach((citation) => {
      if (citation.filename && !names.includes(citation.filename)) names.push(citation.filename);
    });
    if (names.length) {
      const pills = document.createElement("div");
      pills.className = "pills";
      names.forEach((name) => {
        const pill = document.createElement("span");
        pill.className = "pill";
        pill.textContent = name;
        pills.append(pill);
      });
      bubble.append(pills);
    }
    log.append(bubble);
  });
}

function threadButton(thread, active, onOpen, onDelete) {
  const row = document.createElement("div");
  row.className = `nav-item${active ? " is-active" : ""}`;
  const label = document.createElement("span");
  label.textContent = `${active ? "● " : ""}${thread.title || "New chat"}`;
  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "icon-button";
  remove.textContent = "×";
  remove.setAttribute("aria-label", "Delete chat");
  label.addEventListener("click", onOpen);
  remove.addEventListener("click", (event) => {
    event.stopPropagation();
    onDelete();
  });
  row.append(label, remove);
  return row;
}

async function refreshChats() {
  const list = $("#chat-list");
  list.replaceChildren();
  let threads = [];
  try {
    threads = await api("/conversations");
  } catch (_error) {
    return;
  }
  if (!threads.length) {
    const empty = document.createElement("p");
    empty.className = "brand-note";
    empty.textContent = "Nothing saved yet.";
    list.append(empty);
    return;
  }
  threads.forEach((thread) => {
    list.append(threadButton(
      thread,
      thread.thread_id === state.shrutiThreadId,
      () => loadThread(thread.thread_id, "shruti"),
      () => removeThread(thread.thread_id, "shruti"),
    ));
  });
}

async function refreshNotebooks() {
  try {
    state.notebooks = await api("/notebooks");
  } catch (_error) {
    state.notebooks = [];
  }
  const list = $("#notebook-list");
  list.replaceChildren();
  if (!state.notebooks.length) {
    const empty = document.createElement("p");
    empty.className = "brand-note";
    empty.textContent = "No notebooks yet.";
    list.append(empty);
  }
  state.notebooks.forEach((notebook) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `nav-item${notebook.id === state.notebookId ? " is-active" : ""}`;
    const active = notebook.id === state.notebookId ? "● " : "";
    button.textContent = `${active}${notebook.title} (${notebook.document_count})`;
    button.addEventListener("click", () => openNotebook(notebook.id));
    list.append(button);
  });
  const selected = state.notebooks.find((notebook) => notebook.id === state.notebookId);
  $("#notebook-chats").hidden = !selected;
  if (!selected) return;
  const chats = $("#notebook-chat-list");
  chats.replaceChildren();
  let threads = [];
  try {
    threads = await api(`/notebooks/${selected.id}/conversations`);
  } catch (_error) {
    threads = [];
  }
  threads.forEach((thread) => {
    chats.append(threadButton(
      thread,
      thread.thread_id === state.smritiThreadId,
      () => loadThread(thread.thread_id, "smriti"),
      () => removeThread(thread.thread_id, "smriti"),
    ));
  });
}

function render() {
  renderStatus();
  const shrutiEmpty = state.shrutiMessages.length === 0;
  $("#shruti-hero").hidden = !shrutiEmpty;
  renderMessages("#shruti-log", state.shrutiMessages);
  const selected = state.notebooks.find((notebook) => notebook.id === state.notebookId);
  $("#smriti-empty").hidden = Boolean(selected);
  $("#smriti-workspace").hidden = !selected;
  $("#composer").hidden = state.mode === "smriti" && !selected;
  if (selected) {
    $("#notebook-heading").textContent = selected.title;
    $("#rename-input").value = selected.title;
    const sources = $("#source-list");
    sources.replaceChildren();
    if (!state.documents.length) {
      const empty = document.createElement("p");
      empty.className = "lede tight";
      empty.textContent = "No files yet. A scanned PDF with no text layer will be refused.";
      sources.append(empty);
    }
    state.documents.forEach((file) => {
      const card = document.createElement("article");
      card.className = "source";
      const copy = document.createElement("div");
      const name = document.createElement("strong");
      name.textContent = file.filename;
      const meta = document.createElement("p");
      meta.textContent = `${file.chunk_count} chunks`;
      copy.append(name, meta);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "ghost";
      remove.textContent = "Remove";
      remove.addEventListener("click", () => removeDocument(file.id));
      card.append(copy, remove);
      sources.append(card);
    });
  }
  renderMessages("#smriti-log", state.smritiMessages);
}

async function loadThread(threadId, mode) {
  const history = await api(`/conversations/${threadId}`);
  const messages = history.map((item) => ({
    role: item.role,
    content: item.content,
    citations: item.citations || [],
  }));
  if (mode === "shruti") {
    state.shrutiThreadId = threadId;
    state.shrutiMessages = messages;
    await refreshChats();
  } else {
    state.smritiThreadId = threadId;
    state.smritiMessages = messages;
    await refreshNotebooks();
  }
  render();
}

async function removeThread(threadId, mode) {
  if (!window.confirm("Delete this chat?")) return;
  try {
    await api(`/conversations/${threadId}`, { method: "DELETE" });
  } catch (error) {
    notice(error.message);
    return;
  }
  if (mode === "shruti" && threadId === state.shrutiThreadId) {
    state.shrutiThreadId = id("shruti");
    state.shrutiMessages = [];
  }
  if (mode === "smriti" && threadId === state.smritiThreadId) {
    state.smritiThreadId = id(`smriti-${state.notebookId}`);
    state.smritiMessages = [];
  }
  notice("");
  await refreshChats();
  await refreshNotebooks();
  render();
}

async function openNotebook(notebookId) {
  state.notebookId = notebookId;
  state.mode = "smriti";
  try {
    state.documents = await api(`/notebooks/${notebookId}/documents`);
    const threads = await api(`/notebooks/${notebookId}/conversations`);
    if (threads.length) {
      await loadThread(threads[0].thread_id, "smriti");
    } else {
      state.smritiThreadId = id(`smriti-${notebookId}`);
      state.smritiMessages = [];
    }
  } catch (error) {
    notice(error.message);
  }
  setMode("smriti");
  await refreshNotebooks();
  render();
}

async function ask(text) {
  const content = text.trim();
  if (!content || state.busy) return;
  notice("");
  state.busy = true;
  $("#send").disabled = true;
  const shruti = state.mode === "shruti";
  const messages = shruti ? state.shrutiMessages : state.smritiMessages;
  messages.push({ role: "user", content, citations: [] });
  render();
  try {
    const body = shruti
      ? { session_id: state.shrutiThreadId, message: content }
      : { notebook_id: state.notebookId, session_id: state.smritiThreadId, message: content };
    const path = shruti ? "/chat" : "/smriti/chat";
    const result = await api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    messages.push({
      role: "assistant",
      content: result.reply || "",
      citations: result.citations || [],
    });
  } catch (error) {
    messages.pop();
    notice(error.message);
  } finally {
    state.busy = false;
    $("#send").disabled = false;
    render();
    if (shruti) refreshChats();
    else refreshNotebooks();
  }
}

function discardReview() {
  $("#review").hidden = true;
  $("#review-text").value = "";
  if (state.reviewAudioUrl) URL.revokeObjectURL(state.reviewAudioUrl);
  state.reviewAudioUrl = null;
  $("#review-audio").removeAttribute("src");
}

function encodeWav(chunks, sampleRate) {
  const length = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const buffer = new ArrayBuffer(44 + length * 2);
  const view = new DataView(buffer);
  const write = (offset, value) => {
    for (let index = 0; index < value.length; index += 1) {
      view.setUint8(offset + index, value.charCodeAt(index));
    }
  };
  write(0, "RIFF");
  view.setUint32(4, 36 + length * 2, true);
  write(8, "WAVE");
  write(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  write(36, "data");
  view.setUint32(40, length * 2, true);
  let offset = 44;
  chunks.forEach((chunk) => {
    chunk.forEach((sample) => {
      const clamped = Math.max(-1, Math.min(1, sample));
      view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
      offset += 2;
    });
  });
  return new Blob([buffer], { type: "audio/wav" });
}

async function toggleRecording() {
  if (state.recorder) {
    const { context, processor, source, mute, stream, chunks } = state.recorder;
    processor.disconnect();
    source.disconnect();
    mute.disconnect();
    stream.getTracks().forEach((track) => track.stop());
    const sampleRate = context.sampleRate;
    await context.close();
    state.recorder = null;
    $("#mic").classList.remove("is-recording");
    $("#mic").setAttribute("aria-label", "Speak Nepali");
    $("#mic").title = "Speak Nepali";
    const blob = encodeWav(chunks, sampleRate);
    const form = new FormData();
    form.append("file", blob, "voice.wav");
    try {
      const result = await api("/transcribe", { method: "POST", body: form });
      const text = (result.transcription || "").trim();
      if (!text) {
        notice("No speech in that clip. Try again a little closer to the mic.");
        return;
      }
      if (state.reviewAudioUrl) URL.revokeObjectURL(state.reviewAudioUrl);
      state.reviewAudioUrl = URL.createObjectURL(blob);
      $("#review-audio").src = state.reviewAudioUrl;
      $("#review-text").value = text;
      $("#review").hidden = false;
      notice("");
    } catch (error) {
      notice(error.message);
    }
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const context = new AudioContext();
    const source = context.createMediaStreamSource(stream);
    const processor = context.createScriptProcessor(4096, 1, 1);
    const mute = context.createGain();
    mute.gain.value = 0;
    const chunks = [];
    processor.onaudioprocess = (event) => {
      chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
    };
    source.connect(processor);
    processor.connect(mute);
    mute.connect(context.destination);
    state.recorder = { context, processor, source, mute, stream, chunks };
    $("#mic").classList.add("is-recording");
    $("#mic").setAttribute("aria-label", "Stop recording");
    $("#mic").title = "Stop recording";
    notice("");
  } catch (_error) {
    notice("The microphone is not available in this browser.");
  }
}

function bind() {
  $("#mode-shruti").addEventListener("click", () => setMode("shruti"));
  $("#mode-smriti").addEventListener("click", async () => {
    setMode("smriti");
    await refreshNotebooks();
    render();
  });
  $("#new-chat").addEventListener("click", async () => {
    state.shrutiThreadId = id("shruti");
    state.shrutiMessages = [];
    discardReview();
    await refreshChats();
    render();
  });
  $("#new-notebook-chat").addEventListener("click", () => {
    state.smritiThreadId = id(`smriti-${state.notebookId}`);
    state.smritiMessages = [];
    discardReview();
    render();
  });
  $("#create-notebook").addEventListener("submit", async (event) => {
    event.preventDefault();
    const title = $("#notebook-title").value.trim() || "Untitled notebook";
    try {
      const notebook = await api("/notebooks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      $("#notebook-title").value = "";
      await openNotebook(notebook.id);
    } catch (error) {
      notice(error.message);
    }
  });
  $("#upload-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const file = $("#file-input").files[0];
    if (!file || !state.notebookId) return;
    const form = new FormData();
    form.append("file", file);
    try {
      await api(`/notebooks/${state.notebookId}/documents`, { method: "POST", body: form });
      $("#file-input").value = "";
      state.documents = await api(`/notebooks/${state.notebookId}/documents`);
      await refreshNotebooks();
      notice("");
      render();
    } catch (error) {
      notice(error.message);
    }
  });
  $("#rename-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const title = $("#rename-input").value.trim();
    if (!title || !state.notebookId) return;
    try {
      await api(`/notebooks/${state.notebookId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title }),
      });
      await refreshNotebooks();
      render();
    } catch (error) {
      notice(error.message);
    }
  });
  $("#delete-notebook").addEventListener("click", async () => {
    if (!state.notebookId || !window.confirm("Delete this notebook and its files?")) return;
    try {
      await api(`/notebooks/${state.notebookId}`, { method: "DELETE" });
      state.notebookId = null;
      state.documents = [];
      state.smritiMessages = [];
      state.smritiThreadId = null;
      await refreshNotebooks();
      render();
    } catch (error) {
      notice(error.message);
    }
  });
  $("#composer").addEventListener("submit", (event) => {
    event.preventDefault();
    const text = $("#message").value;
    $("#message").value = "";
    ask(text);
  });
  $("#message").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      $("#composer").requestSubmit();
    }
  });
  $("#mic").addEventListener("click", toggleRecording);
  $("#review-send").addEventListener("click", () => {
    const text = $("#review-text").value;
    discardReview();
    ask(text);
  });
  $("#review-discard").addEventListener("click", discardReview);
  const suggestions = $("#suggestions");
  SUGGESTIONS.forEach(([label, prompt]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", () => ask(prompt));
    suggestions.append(button);
  });
}

async function removeDocument(documentId) {
  try {
    await api(`/notebooks/${state.notebookId}/documents/${documentId}`, { method: "DELETE" });
    state.documents = await api(`/notebooks/${state.notebookId}/documents`);
    await refreshNotebooks();
    render();
  } catch (error) {
    notice(error.message);
  }
}

async function boot() {
  bind();
  try {
    state.health = await api("/health");
  } catch (_error) {
    state.health = null;
  }
  await refreshChats();
  render();
}

boot();
