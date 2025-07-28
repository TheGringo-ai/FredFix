document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const fileInput = document.getElementById("file-input");
  const chatContainer = document.getElementById("chat-container");
  const analyzeFolderBtn = document.getElementById("analyze-folder-btn");
  const modelSelect = document.getElementById("model-select");
  const agentSelect = document.getElementById("agent-select");
  const micButton = document.getElementById("mic-button");
  const resetBtn = document.getElementById("reset-btn");
  const fileListBtn = document.getElementById("file-list-btn");
  const fileListBox = document.getElementById("file-list-box");

  const apiHost = window.location.hostname === "localhost" ? "http://localhost:8000" : "";
  const isVSCode = navigator.userAgent.includes("vscode");
  const isCLI = window.location.search.includes("cli=true");

  if (isVSCode || isCLI) {
    document.body.classList.add("cli-mode");
  }

  // --- Message Handling ---
  function addMessage(content, isUser = true, isCode = false) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("chat-message", isUser ? "user-message" : "bot-message");

    const contentDiv = document.createElement("div");
    contentDiv.classList.add("message-content");

    if (isCode) {
      contentDiv.innerHTML = `<pre><code class="language-python">${content}</code></pre>`;
    } else {
      contentDiv.innerHTML = marked.parse(content);
    }
    
    const metaDiv = document.createElement("div");
    metaDiv.classList.add("message-meta");
    metaDiv.textContent = `${isUser ? "You" : "Fred"} • ${new Date().toLocaleTimeString()}`;

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(metaDiv);
    chatContainer.appendChild(messageDiv);

    // Animation and scroll
    setTimeout(() => messageDiv.classList.add("show"), 10);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Syntax highlighting
    if (isCode) {
      hljs.highlightElement(messageDiv.querySelector("code"));
    }
  }

  function addBotMessageStreaming() {
    const botMessageDiv = document.createElement("div");
    botMessageDiv.classList.add("chat-message", "bot-message");

    const contentDiv = document.createElement("div");
    contentDiv.classList.add("message-content");
    botMessageDiv.appendChild(contentDiv);
    
    const metaDiv = document.createElement("div");
    metaDiv.classList.add("message-meta");
    metaDiv.textContent = `Fred • ${new Date().toLocaleTimeString()}`;
    botMessageDiv.appendChild(metaDiv);

    chatContainer.appendChild(botMessageDiv);
    setTimeout(() => botMessageDiv.classList.add("show"), 10);

    return contentDiv;
  }

  // --- Form & Button Event Handlers ---
  chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const userMessage = userInput.value.trim();
    const file = fileInput.files[0];

    if (!userMessage && !file) return;

    addMessage(userMessage || `File: ${file.name}`, true);
    userInput.value = "";
    fileInput.value = "";

    // Show typing indicator
    const typingIndicator = document.createElement("div");
    typingIndicator.classList.add("typing-indicator");
    typingIndicator.innerHTML = `<span></span><span></span><span></span>`;
    chatContainer.appendChild(typingIndicator);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {
      if (file) {
        await handleFileUpload(file);
      } else {
        await handleTextMessage(userMessage);
      }
    } catch (error) {
      addMessage(`Error: ${error.message}`, false);
    } finally {
      chatContainer.removeChild(typingIndicator);
    }
  });

  async function handleTextMessage(message) {
    const response = await fetch(`${apiHost}/chat-stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        messages: [{ role: "user", content: message }],
        agent: agentSelect?.value || "chat",
        source: isVSCode ? "vscode" : isCLI ? "cli" : "web",
      }),
    });

    if (!response.body) throw new Error("No response body");

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    const botMessageContent = addBotMessageStreaming();
    let fullResponse = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      fullResponse += chunk;
      botMessageContent.innerHTML = marked.parse(fullResponse);
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    // Final highlighting after stream is complete
    botMessageContent.querySelectorAll('pre code').forEach((block) => {
        hljs.highlightElement(block);
    });
  }

  async function handleFileUpload(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${apiHost}/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed with status ${response.status}`);
    }

    const result = await response.json();
    addMessage(result.analysis, false, true);
  }

  if (resetBtn) {
    resetBtn.addEventListener("click", async () => {
      try {
        await fetch(`${apiHost}/reset`, { method: "POST" });
        chatContainer.innerHTML = "";
        addMessage("Chat history has been reset.", false);
      } catch (e) {
        addMessage("Failed to reset chat history.", false);
      }
    });
  }

  if (fileListBtn) {
    fileListBtn.addEventListener("click", async () => {
      fileListBox.innerHTML = "📁 Loading file list...";
      try {
        const res = await fetch(`${apiHost}/files`);
        if (!res.ok) throw new Error("Failed to fetch file list");
        const data = await res.json();
        fileListBox.innerHTML = "";
        data.files.forEach((file) => {
          const item = document.createElement("div");
          item.className = "file-entry";
          item.textContent = file;
          item.addEventListener("click", () => {
            userInput.value = `Let's work on the file: ${file}`;
          });
          fileListBox.appendChild(item);
        });
      } catch (err) {
        fileListBox.innerHTML = `❌ Error: ${err.message}`;
      }
    });
  }

  // Voice input handling
  if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const recognition = new (window.webkitSpeechRecognition || window.SpeechRecognition)();
    recognition.continuous = false;
    recognition.interimResults = false;

    micButton.addEventListener("click", () => {
      if (micButton.classList.contains("active")) {
        recognition.stop();
      } else {
        recognition.start();
      }
    });
    recognition.onstart = () => micButton.classList.add("active");
    recognition.onend = () => micButton.classList.remove("active");
    recognition.onresult = (event) => {
      userInput.value = event.results[0][0].transcript;
    };
    recognition.onerror = (event) => {
      console.error("Speech recognition error", event.error);
      micButton.classList.remove("active");
    };
  } else {
    micButton.style.display = "none";
  }
});