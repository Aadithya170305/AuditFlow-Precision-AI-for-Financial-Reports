const fileInput   = document.getElementById("fileInput");
const userInput   = document.getElementById("userInput");
const sendBtn     = document.getElementById("sendBtn");
const chatDisplay = document.getElementById("chat-display");
const hero        = document.getElementById("hero");
let chatStarted = false;
let isWaiting   = false;
function openFilePicker() {
    fileInput.click();
}
function showAlert(message, type = "success") {
    const el = document.createElement("div");
    el.className = `custom-alert ${type}`;
    el.innerText = message;
    document.body.appendChild(el);
    setTimeout(() => setTimeout(() => el.remove(), 400), 2500);
}
fileInput.addEventListener("change", async function () {
    const file = this.files[0];
    if (!file) return;
    if (file.type !== "application/pdf") { 
        showAlert("Please upload a PDF file", "error"); 
        return; 
    }
    showAlert(`Uploading ${file.name}...`, "info");
    const formData = new FormData();
    formData.append("file", file);
    try {
        const response = await fetch("/upload-pdf", { method: "POST", body: formData });
        const data = await response.json();
        response.ok ? showAlert("PDF processed successfully", "success")
                    : showAlert("Upload failed: " + (data.detail || "Error"), "error");
        this.value = "";
    } catch { showAlert("Connection error", "error"); }
});
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message || isWaiting) {
        return;
    }
    isWaiting = true;
    sendBtn.style.opacity = "0.4";
    if (!chatStarted) {
        chatStarted = true;
        hero.classList.add("hidden");
        chatDisplay.style.display = "flex";
    }
    appendMessage(message, "user");
    userInput.value = "";
    const typingId = showTyping();
    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json" 
            },
            body: JSON.stringify({
                 msg: message 
            })
        });
        removeTyping(typingId);
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            showAlert("Server error: " + (errData.detail || response.status), "error");
            return;
        }
        const data = await response.json();
        let reply = "";
        if (typeof data === "string") {
            reply = data;
        } 
        else if (data.reply) {
            const r = data.reply;
            if (typeof r === "string")  {
                reply = r;
            }
            else if (r.choices?.[0]?.message?.content)  {
                reply = r.choices[0].message.content;
            }
            else if (r.content) {
                reply = r.content;
            }
            else  {
                reply = JSON.stringify(r);
            }
        } 
        else if (data.choices?.[0]?.message?.content) {
            reply = data.choices[0].message.content;
        }
        else if (data.content){
            reply = data.content;
        }
        else if (data.message) {
            reply = data.message;
        }
        else if (data.response) {
            reply = data.response;
        }
        else if (data.answer) {
            reply = data.answer;
        }
        else {
            reply = JSON.stringify(data, null, 2);
        }
        appendMessage(reply);
    } 
    catch (err) {
        removeTyping(typingId);
        console.error("Fetch error:", err);
        showAlert("Network error — check console", "error");
    } 
    finally {
        isWaiting = false;
        sendBtn.style.opacity = "1";
    }
}
function appendMessage(text, sender) {
    const row = document.createElement("div");
    row.className = `message-row ${sender}`;
    if (sender === "user") {
        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        bubble.innerText = text;
        row.appendChild(bubble);
    } 
    else {
        const icon = document.createElement("div");
        const bubble = document.createElement("div");
        bubble.className = "message-bubble md";
        marked.setOptions({
            highlight: (code, lang) => {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return hljs.highlightAuto(code).value;
            },
            breaks: true,
            gfm: true
        });
        bubble.innerHTML = marked.parse(text);
        bubble.querySelectorAll("pre code").forEach(block => {
            hljs.highlightElement(block);
        });
        row.appendChild(bubble);
    }
    chatDisplay.appendChild(row);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
}

function showTyping() {
    const id = "typing-" + Date.now();
    const row = document.createElement("div");
    row.className = "message-row ai";
    row.id = id;
    const icon = document.createElement("div");
    const bubble = document.createElement("div");
    bubble.className = "message-bubble typing-bubble";
    bubble.innerHTML = `<span></span><span></span><span></span>`;
    row.appendChild(bubble);
    chatDisplay.appendChild(row);
    chatDisplay.scrollTop = chatDisplay.scrollHeight;
    return id;
}
function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) {
        el.remove();
    }
}
sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});