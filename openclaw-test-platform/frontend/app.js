const API_BASE = '';

let sessionId = localStorage.getItem('oc_session_id') || null;
let currentOptions = [];
let isMultiSelect = false;
let selectedValues = [];

const chatMessages = document.getElementById('chatMessages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const optionsArea = document.getElementById('optionsArea');
const inputArea = document.getElementById('inputArea');
const cardPreview = document.getElementById('cardPreview');
const cardActions = document.getElementById('cardActions');
const statusEl = document.getElementById('status');

// ============ 初始化 ============

async function init() {
    if (!sessionId) {
        const res = await fetch(`${API_BASE}/api/restart`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        const data = await res.json();
        sessionId = data.session_id;
        localStorage.setItem('oc_session_id', sessionId);
        renderMessages(data.messages);
        updateProgress(data.progress);
    } else {
        // 有 session，发一个空消息获取当前状态
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message: '' })
        });
        const data = await res.json();
        if (data.done) {
            renderMessages(data.messages);
            if (data.card) renderCard(data.card);
        } else {
            // 重新开始
            await restart();
        }
    }
}

// ============ 消息渲染 ============

function renderMessages(messages) {
    messages.forEach(msg => appendMessage(msg));
    scrollToBottom();
}

function appendMessage(msg, isUser = false) {
    const div = document.createElement('div');
    div.className = `message ${isUser ? 'user' : 'bot'}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = isUser ? '👤' : '🤖';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    if (msg.type === 'summary') {
        // 汇总消息特殊渲染
        const title = document.createElement('div');
        title.style.fontWeight = '600';
        title.style.marginBottom = '8px';
        title.textContent = '📋 信息汇总';
        content.appendChild(title);
        
        const sub = document.createElement('div');
        sub.style.marginBottom = '10px';
        sub.style.color = 'var(--text-secondary)';
        sub.textContent = '请确认是否有误：';
        content.appendChild(sub);
        
        const box = document.createElement('div');
        box.className = 'summary-box';
        
        const lines = msg.content.split('\n');
        lines.forEach(line => {
            if (!line.trim() || line.includes('信息汇总') || line.includes('请确认')) return;
            const item = document.createElement('div');
            item.className = 'summary-item';
            const parts = line.split('：');
            if (parts.length >= 2) {
                const key = document.createElement('span');
                key.className = 'key';
                key.textContent = parts[0].replace('· ', '').trim() + '：';
                const val = document.createElement('span');
                val.className = 'value';
                val.textContent = parts.slice(1).join('：');
                item.appendChild(key);
                item.appendChild(val);
            } else {
                item.textContent = line;
            }
            box.appendChild(item);
        });
        content.appendChild(box);
    } else {
        content.textContent = msg.content;
    }
    
    div.appendChild(avatar);
    div.appendChild(content);
    chatMessages.appendChild(div);
    
    // 处理选项
    if (msg.options && msg.options.length > 0) {
        currentOptions = msg.options;
        renderOptions(msg.options);
    } else {
        currentOptions = [];
        optionsArea.style.display = 'none';
        inputArea.style.display = 'flex';
    }
    
    scrollToBottom();
}

function addUserMessage(text) {
    appendMessage({ type: 'text', content: text }, true);
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ============ 选项按钮 ============

function renderOptions(options) {
    optionsArea.innerHTML = '';
    optionsArea.style.display = 'flex';
    
    // 判断是否是多选场景（合作类型、资源等）
    const lastMsg = chatMessages.lastElementChild;
    const msgText = lastMsg ? lastMsg.querySelector('.message-content').textContent : '';
    isMultiSelect = msgText.includes('可多选') || msgText.includes('可多选，用逗号分隔');
    selectedValues = [];
    
    if (isMultiSelect) {
        inputArea.style.display = 'flex';
    } else {
        inputArea.style.display = 'none';
    }
    
    options.forEach(opt => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.textContent = opt.label;
        btn.onclick = () => handleOptionClick(opt.value, btn);
        optionsArea.appendChild(btn);
    });
    
    if (isMultiSelect) {
        const confirmBtn = document.createElement('button');
        confirmBtn.className = 'option-btn confirm';
        confirmBtn.textContent = '✅ 确认选择';
        confirmBtn.onclick = () => {
            if (selectedValues.length > 0) {
                sendMessage(selectedValues.join('，'));
            }
        };
        optionsArea.appendChild(confirmBtn);
    }
}

function handleOptionClick(value, btn) {
    if (isMultiSelect) {
        btn.classList.toggle('selected');
        if (btn.classList.contains('selected')) {
            selectedValues.push(value);
        } else {
            selectedValues = selectedValues.filter(v => v !== value);
        }
    } else {
        sendMessage(value);
    }
}

// ============ 发送消息 ============

async function sendMessage(text) {
    if (!text.trim()) return;
    
    addUserMessage(text);
    setLoading(true);
    
    try {
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message: text })
        });
        const data = await res.json();
        
        renderMessages(data.messages);
        updateProgress(data.progress);
        
        if (data.card) {
            renderCard(data.card);
        }
        
        if (data.done) {
            cardActions.style.display = 'flex';
        }
    } catch (err) {
        appendMessage({ type: 'text', content: '⚠️ 网络错误，请重试' });
    } finally {
        setLoading(false);
    }
}

function setLoading(loading) {
    sendBtn.disabled = loading;
    userInput.disabled = loading;
    statusEl.textContent = loading ? '思考中...' : '在线';
    statusEl.style.color = loading ? 'var(--warning)' : 'var(--success)';
}

// ============ 进度条 ============

function updateProgress(percent) {
    let bar = document.querySelector('.progress-bar');
    if (!bar) {
        bar = document.createElement('div');
        bar.className = 'progress-bar';
        const fill = document.createElement('div');
        fill.className = 'progress-fill';
        fill.id = 'progressFill';
        bar.appendChild(fill);
        chatMessages.parentNode.insertBefore(bar, chatMessages);
    }
    document.getElementById('progressFill').style.width = percent + '%';
}

// ============ 卡片渲染 ============

function renderCard(card) {
    const roleClass = card.role || 'founder';
    const roleLabel = card.role_label || '创业者';
    const tracks = card.tracks ? card.tracks.split('，').join(' · ').split(',').join(' · ') : '';
    
    const tagsHtml = (card.tags || []).map(t => {
        const typeClass = t.type === 'domain' ? 'tag-domain' : 
                         t.type === 'skill' ? 'tag-skill' : 
                         t.type === 'need' ? 'tag-need' : 'tag-match';
        return `<span class="tag ${typeClass}">${t.text}</span>`;
    }).join('');
    
    const coopTypes = card.coop_types ? card.coop_types.split('，').join(' · ').split(',').join(' · ') : '';
    
    cardPreview.innerHTML = `
        <div class="id-card">
            <div class="id-card-header">
                <div class="id-card-avatar">${card.avatar}</div>
                <div class="id-card-meta">
                    <div class="id-card-name">${card.nickname}</div>
                    <span class="id-card-role ${roleClass}">${roleLabel}</span>
                </div>
            </div>
            <div class="id-card-body">
                <div class="id-card-row">
                    <span class="label">📍</span> ${card.city} <span class="label">|</span> 🏷️ ${tracks}
                </div>
                <div class="id-card-row">
                    <span class="label">💬</span> ${card.slogan}
                </div>
                <div class="id-card-row">
                    ${card.row4}
                </div>
                <div class="id-card-row">
                    ${card.row5}
                </div>
                <div class="id-card-row">
                    <span class="label">🤝</span> ${coopTypes}
                </div>
            </div>
            <div class="id-card-tags">
                ${tagsHtml}
            </div>
        </div>
    `;
    
    cardActions.style.display = 'flex';
}

// ============ 事件绑定 ============

sendBtn.addEventListener('click', () => {
    sendMessage(userInput.value);
    userInput.value = '';
});

userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage(userInput.value);
        userInput.value = '';
    }
});

document.getElementById('copyCard').addEventListener('click', () => {
    const cardEl = document.querySelector('.id-card');
    if (cardEl) {
        const text = cardEl.innerText;
        navigator.clipboard.writeText(text).then(() => {
            alert('卡片内容已复制到剪贴板');
        });
    }
});

document.getElementById('downloadCard').addEventListener('click', async () => {
    if (!sessionId) return;
    const res = await fetch(`${API_BASE}/api/cards`);
    const cards = await res.json();
    if (cards.length > 0) {
        const blob = new Blob([JSON.stringify(cards[0], null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `card_${cards[0].nickname}.json`;
        a.click();
    }
});

document.getElementById('restartBtn').addEventListener('click', restart);

async function restart() {
    chatMessages.innerHTML = '';
    cardPreview.innerHTML = `
        <div class="card-placeholder">
            <p>完成信息采集后将在此生成卡片</p>
        </div>
    `;
    cardActions.style.display = 'none';
    optionsArea.style.display = 'none';
    inputArea.style.display = 'flex';
    
    const res = await fetch(`${API_BASE}/api/restart`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId })
    });
    const data = await res.json();
    sessionId = data.session_id;
    localStorage.setItem('oc_session_id', sessionId);
    renderMessages(data.messages);
    updateProgress(0);
}

// ============ 启动 ============

init();
