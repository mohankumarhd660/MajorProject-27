(function () {
  const chatWindow = document.getElementById('chatWindow');
  const input = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendBtn');

  if (!chatWindow || !input || !sendBtn) return;

  let threadId = 'default';

  function scrollToBottom() {
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }

  function addMessage(role, content) {
    const wrap = document.createElement('div');
    wrap.className = 'msg ' + (role === 'user' ? 'user' : 'ai');

    const text = document.createElement('div');
    text.className = 'msg-text';
    text.textContent = content;
    wrap.appendChild(text);

    chatWindow.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  async function typeInto(el, fullText) {
    const textEl = el.firstChild;
    textEl.textContent = '';
    const speed = 10;
    for (let i = 0; i < fullText.length; i++) {
      textEl.textContent += fullText[i];
      if (i % 6 === 0) scrollToBottom();
      await new Promise(r => setTimeout(r, speed));
    }
    scrollToBottom();
  }

  async function send() {
    const msg = input.value.trim();
    if (!msg) return;

    input.value = '';
    addMessage('user', msg);

    const typing = addMessage('assistant', 'Typing...');

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg, thread_id: threadId })
      });

      const ct = (resp.headers.get('content-type') || '').toLowerCase();
      let data = null;
      if (ct.includes('application/json')) {
        data = await resp.json();
      } else {
        const text = await resp.text();
        throw new Error(text.slice(0, 160));
      }
      if (!resp.ok) throw new Error((data && data.error) || 'Request failed');

      typing.remove();
      const bubble = addMessage('assistant', '');
      await typeInto(bubble, App.cleanAssistantText(data.reply));
    } catch (e) {
      typing.remove();
      addMessage('assistant', 'Unable to process your request right now. ' + e.message);
    }
  }

  sendBtn.addEventListener('click', send);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') send();
  });
})();
