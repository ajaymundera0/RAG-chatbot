const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const statusMsg = document.getElementById('upload-status');
const docList = document.getElementById('doc-list');

const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const messagesContainer = document.getElementById('messages-container');
const sendBtn = document.getElementById('send-btn');
const stopBtn = document.getElementById('stop-btn');

let currentAbortController = null;

stopBtn.addEventListener('click', () => {
    if (currentAbortController) {
        currentAbortController.abort();
    }
});

// --- File Upload Logic ---
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        uploadFile(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        uploadFile(e.target.files[0]);
    }
});

async function uploadFile(file) {
    statusMsg.className = 'status-msg loading';
    statusMsg.textContent = 'Uploading and processing...';
    
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (response.ok) {
            statusMsg.className = 'status-msg success';
            statusMsg.textContent = 'File processed successfully!';
            
            // Add to list
            const li = document.createElement('li');
            li.innerHTML = `<i class="fa-regular fa-file-lines"></i> ${file.name}`;
            docList.appendChild(li);
        } else {
            throw new Error(data.detail || 'Upload failed');
        }
    } catch (err) {
        statusMsg.className = 'status-msg error';
        statusMsg.textContent = err.message;
    }

    // Hide status after 5s
    setTimeout(() => {
        statusMsg.className = 'status-msg hidden';
    }, 5000);
}


// --- Chat Logic ---
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    // Add user message
    appendMessage(query, 'user');
    chatInput.value = '';
    
    // Add AI message placeholder with typing indicator
    const { bubble, contentDiv } = appendAIMessagePlaceholder();
    sendBtn.disabled = true;
    sendBtn.classList.add('hidden');
    stopBtn.classList.remove('hidden');

    currentAbortController = new AbortController();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query, top_k: 4 }),
            signal: currentAbortController.signal
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Chat failed');
        }

        // Stream reader
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let fullResponse = "";

        // Remove typing indicator, ready to inject text
        bubble.innerHTML = '<div class="content"></div>';
        const newContentDiv = bubble.querySelector('.content');

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value, { stream: true });
            fullResponse += chunk;
            
            if (fullResponse.includes("___SOURCES___")) {
                const parts = fullResponse.split("___SOURCES___");
                const markdownText = parts[0];
                newContentDiv.innerHTML = marked.parse(markdownText);
                
                try {
                    const sourcesJsonStr = parts[1].trim();
                    if (sourcesJsonStr) {
                        const sources = JSON.parse(sourcesJsonStr);
                        renderSources(bubble, sources);
                    }
                } catch (e) {
                    // JSON might not be fully streamed yet, ignore until next chunk
                }
            } else {
                // Render markdown on the fly
                newContentDiv.innerHTML = marked.parse(fullResponse);
            }
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }

    } catch (err) {
        if (err.name === 'AbortError') {
            const stopSpan = document.createElement('span');
            stopSpan.style = "color: var(--text-muted); font-style: italic; display: block; margin-top: 8px;";
            stopSpan.innerText = "Generation stopped by user.";
            bubble.appendChild(stopSpan);
            
            if (contentDiv && contentDiv.parentNode === bubble) {
                contentDiv.remove();
            }
        } else {
            const errorMsg = `<span style="color: #ef4444;">Error: ${err.message}</span>`;
            const content = bubble.querySelector('.content');
            if (content) {
                content.innerHTML += `<br>${errorMsg}`;
            } else {
                bubble.innerHTML = errorMsg;
            }
        }
    } finally {
        currentAbortController = null;
        sendBtn.disabled = false;
        sendBtn.classList.remove('hidden');
        stopBtn.classList.add('hidden');
        chatInput.focus();
    }
});

function appendMessage(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-message`;

    const icon = sender === 'user' ? 'fa-user' : 'fa-robot';
    
    msgDiv.innerHTML = `
        <div class="avatar"><i class="fa-solid ${icon}"></i></div>
        <div class="bubble"></div>
    `;
    
    // Use marked for user as well to allow basic bolding if they typed it
    msgDiv.querySelector('.bubble').textContent = text; 
    
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendAIMessagePlaceholder() {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ai-message`;

    msgDiv.innerHTML = `
        <div class="avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="bubble">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    return { bubble: msgDiv.querySelector('.bubble'), contentDiv: msgDiv.querySelector('.typing-indicator') };
}

function renderSources(bubble, sources) {
    if (bubble.querySelector('.sources-container')) return;
    if (!sources || sources.length === 0) return;
    
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'sources-container';
    
    let html = '<h4><i class="fa-solid fa-book-open"></i> Sources Used</h4><div class="sources-list">';
    
    sources.forEach((src, idx) => {
        const meta = src.metadata || {};
        const filename = meta.source || `Source ${idx+1}`;
        const page = meta.page || "1";
        const textSnippet = src.text.substring(0, 200) + "...";
        
        html += `
            <details class="source-card">
                <summary>
                    <span class="src-title"><i class="fa-regular fa-file"></i> ${filename}</span>
                    <span class="src-page">Page ${page}</span>
                </summary>
                <div class="src-content">${textSnippet}</div>
            </details>
        `;
    });
    
    html += '</div>';
    sourcesDiv.innerHTML = html;
    bubble.appendChild(sourcesDiv);
}
