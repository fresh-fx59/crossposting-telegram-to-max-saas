"""Max Bot API Emulator.

Emulates the Max messenger platform API endpoints used by the crossposter backend.
Stores received messages in memory and provides a real-time web UI to view them.
"""

import asyncio
import base64
import json
import time
import uuid
from collections import deque
from datetime import datetime, timezone

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse

app = FastAPI(title="Max Bot API Emulator")

# In-memory storage
messages: deque[dict] = deque(maxlen=200)
uploads: dict[str, dict] = {}
sse_clients: list[asyncio.Queue] = []


def get_token(request: Request, access_token: str | None = None) -> str | None:
    """Extract token from query param or Authorization header."""
    if access_token:
        return access_token
    auth = request.headers.get("Authorization")
    if auth:
        return auth.removeprefix("Bearer ").strip()
    return None


async def broadcast_event(event_data: dict):
    """Send event to all connected SSE clients."""
    data = json.dumps(event_data, ensure_ascii=False)
    dead = []
    for q in sse_clients:
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        sse_clients.remove(q)


# ── Max Bot API Endpoints ──────────────────────────────────────────


@app.get("/me")
async def get_bot_info(request: Request, access_token: str | None = Query(None)):
    """Return fake bot info."""
    token = get_token(request, access_token)
    return {
        "user_id": 1000000,
        "name": "Emulator Bot",
        "username": "emulator_bot",
        "is_bot": True,
        "last_activity_time": int(time.time() * 1000),
    }


@app.post("/messages")
async def send_message(
    request: Request,
    access_token: str | None = Query(None),
    chat_id: int | None = Query(None),
):
    """Receive a message (text or with attachments)."""
    token = get_token(request, access_token)
    body = await request.json()

    msg_id = str(uuid.uuid4())[:12]
    ts = datetime.now(timezone.utc).isoformat()

    # Resolve photo thumbnail from uploads if present
    photo_thumbnail = None
    attachments = body.get("attachments", [])
    for att in attachments:
        if att.get("type") == "image":
            payload = att.get("payload", {})
            upload_id = payload.get("token") or payload.get("id")
            if upload_id and upload_id in uploads:
                photo_thumbnail = uploads[upload_id].get("thumbnail")

    stored = {
        "id": msg_id,
        "timestamp": ts,
        "token": (token or "")[:8] + "..." if token else "none",
        "chat_id": chat_id,
        "text": body.get("text"),
        "attachments": attachments,
        "photo_thumbnail": photo_thumbnail,
        "raw_body": body,
    }
    messages.appendleft(stored)
    await broadcast_event({"type": "message", "data": stored})

    return {
        "message": {
            "body": body,
            "link": None,
            "sender": {"user_id": 1000000, "name": "Emulator Bot"},
            "recipient": {"chat_id": chat_id, "chat_type": "channel"},
            "timestamp": int(time.time() * 1000),
            "stat": {"views": 0},
        },
        "message_id": msg_id,
    }


@app.post("/uploads")
async def upload_file(
    request: Request,
    access_token: str | None = Query(None),
    chat_id: int | None = Query(None),
    type: str | None = Query(None),
):
    """Receive a file upload."""
    token = get_token(request, access_token)
    raw = await request.body()

    upload_token = str(uuid.uuid4())[:16]
    content_type = request.headers.get("content-type", "application/octet-stream")

    # Store a base64 thumbnail for images
    thumbnail = None
    if content_type.startswith("image/"):
        thumbnail = f"data:{content_type};base64,{base64.b64encode(raw).decode()}"

    upload_data = {
        "token": upload_token,
        "type": type or "file",
        "size": len(raw),
        "content_type": content_type,
        "chat_id": chat_id,
        "thumbnail": thumbnail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    uploads[upload_token] = upload_data

    log_entry = {
        "id": upload_token,
        "timestamp": upload_data["timestamp"],
        "token": (get_token(request, access_token) or "")[:8] + "...",
        "chat_id": chat_id,
        "text": f"[Upload: {type or 'file'}, {len(raw)} bytes, {content_type}]",
        "attachments": [],
        "photo_thumbnail": thumbnail,
        "raw_body": {"upload_type": type, "size": len(raw)},
    }
    messages.appendleft(log_entry)
    await broadcast_event({"type": "message", "data": log_entry})

    return {
        "token": upload_token,
        "id": upload_token,
        "type": type or "file",
    }


# ── SSE Stream ─────────────────────────────────────────────────────


@app.get("/emulator/stream")
async def sse_stream():
    """Server-Sent Events stream for real-time updates."""
    q: asyncio.Queue = asyncio.Queue(maxsize=50)
    sse_clients.append(q)

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'connected'})}\n\n"
            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=30)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if q in sse_clients:
                sse_clients.remove(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream",
            "Transfer-Encoding": "chunked",
        },
    )


# ── JSON API for dashboard ─────────────────────────────────────────


@app.get("/emulator/messages")
async def get_messages():
    """Return all stored messages."""
    return {"messages": list(messages), "total": len(messages)}


@app.post("/emulator/clear")
async def clear_messages():
    """Clear all stored messages and uploads."""
    messages.clear()
    uploads.clear()
    await broadcast_event({"type": "cleared"})
    return {"status": "ok"}


# ── Web UI ─────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Real-time dashboard showing received messages."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Max API Emulator</title>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --border: #2a2d3a;
    --text: #e1e4ed;
    --muted: #8b8fa3;
    --accent: #6c5ce7;
    --green: #00b894;
    --red: #e17055;
    --blue: #0984e3;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }
  .header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 16px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    position: sticky;
    top: 0;
    z-index: 10;
  }
  .header h1 {
    font-size: 18px;
    font-weight: 600;
    letter-spacing: -0.5px;
  }
  .header h1 span { color: var(--accent); }
  .status {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
  }
  .dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--red);
  }
  .dot.connected { background: var(--green); }
  .controls {
    display: flex;
    gap: 8px;
  }
  .btn {
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    font-family: inherit;
    transition: all 0.15s;
  }
  .btn:hover { border-color: var(--accent); color: var(--accent); }
  .btn.danger:hover { border-color: var(--red); color: var(--red); }
  .counter {
    font-size: 13px;
    color: var(--muted);
    padding: 0 12px;
  }
  .messages {
    padding: 16px 24px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .msg {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 18px;
    animation: slideIn 0.2s ease-out;
  }
  @keyframes slideIn {
    from { opacity: 0; transform: translateY(-8px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .msg-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
    font-size: 12px;
    color: var(--muted);
  }
  .msg-id { color: var(--accent); font-weight: 600; }
  .msg-chat { color: var(--blue); }
  .msg-time { margin-left: auto; }
  .msg-body {
    font-size: 14px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .msg-photo {
    margin-top: 10px;
    max-width: 320px;
    border-radius: 6px;
    border: 1px solid var(--border);
  }
  .msg-raw {
    margin-top: 10px;
    padding: 10px;
    background: var(--bg);
    border-radius: 6px;
    font-size: 11px;
    color: var(--muted);
    overflow-x: auto;
    display: none;
  }
  .msg-raw.open { display: block; }
  .toggle-raw {
    font-size: 11px;
    color: var(--muted);
    background: none;
    border: none;
    cursor: pointer;
    margin-top: 6px;
    font-family: inherit;
  }
  .toggle-raw:hover { color: var(--accent); }
  .empty {
    text-align: center;
    color: var(--muted);
    padding: 80px 20px;
    font-size: 14px;
  }
  .empty p:first-child {
    font-size: 40px;
    margin-bottom: 16px;
  }
</style>
</head>
<body>

<div class="header">
  <h1><span>Max API</span> Emulator</h1>
  <div style="display:flex;align-items:center;gap:16px;">
    <div class="status">
      <div class="dot" id="statusDot"></div>
      <span id="statusText">Connecting...</span>
    </div>
    <span class="counter" id="counter">0 messages</span>
    <div class="controls">
      <button class="btn danger" onclick="clearMessages()">Clear</button>
    </div>
  </div>
</div>

<div class="messages" id="messageList">
  <div class="empty" id="emptyState">
    <p>📡</p>
    <p>Waiting for messages...</p>
    <p style="margin-top:8px;font-size:12px;">
      Send requests to this server's <code>/messages</code> or <code>/uploads</code> endpoints
    </p>
  </div>
</div>

<script>
let msgCount = 0;

function formatTime(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString('en-GB', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
}

function renderMsg(msg) {
  const el = document.createElement('div');
  el.className = 'msg';
  const rawId = 'raw-' + msg.id;

  let photoHtml = '';
  if (msg.photo_thumbnail) {
    photoHtml = '<img class="msg-photo" src="' + msg.photo_thumbnail + '" alt="uploaded photo">';
  }

  let attachInfo = '';
  if (msg.attachments && msg.attachments.length > 0) {
    attachInfo = ' | ' + msg.attachments.length + ' attachment(s)';
  }

  el.innerHTML =
    '<div class="msg-header">' +
      '<span class="msg-id">#' + msg.id + '</span>' +
      '<span class="msg-chat">chat:' + (msg.chat_id || '?') + '</span>' +
      '<span>token:' + (msg.token || '?') + '</span>' +
      attachInfo +
      '<span class="msg-time">' + formatTime(msg.timestamp) + '</span>' +
    '</div>' +
    '<div class="msg-body">' + escapeHtml(msg.text || '(no text)') + '</div>' +
    photoHtml +
    '<button class="toggle-raw" onclick="toggleRaw(&quot;' + rawId + '&quot;)">show raw</button>' +
    '<div class="msg-raw" id="' + rawId + '">' + escapeHtml(JSON.stringify(msg.raw_body, null, 2)) + '</div>';

  return el;
}

function escapeHtml(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function toggleRaw(id) {
  document.getElementById(id).classList.toggle('open');
}

function addMessage(msg) {
  const list = document.getElementById('messageList');
  const empty = document.getElementById('emptyState');
  if (empty) empty.remove();
  list.prepend(renderMsg(msg));
  msgCount++;
  document.getElementById('counter').textContent = msgCount + ' message' + (msgCount !== 1 ? 's' : '');
}

async function loadExisting() {
  try {
    const res = await fetch('/emulator/messages');
    const data = await res.json();
    msgCount = 0;
    data.messages.reverse().forEach(m => addMessage(m));
  } catch(e) {
    console.error('Failed to load messages:', e);
  }
}

async function clearMessages() {
  await fetch('/emulator/clear', {method: 'POST'});
  document.getElementById('messageList').innerHTML =
    '<div class="empty" id="emptyState"><p>📡</p><p>Waiting for messages...</p></div>';
  msgCount = 0;
  document.getElementById('counter').textContent = '0 messages';
}

let lastMsgId = null;
let pollActive = false;

async function poll() {
  const dot = document.getElementById('statusDot');
  const txt = document.getElementById('statusText');
  pollActive = true;
  dot.classList.add('connected');
  txt.textContent = 'Polling (2s)';

  while (pollActive) {
    try {
      const res = await fetch('/emulator/messages');
      const data = await res.json();
      dot.classList.add('connected');
      txt.textContent = 'Polling (2s)';
      if (data.total === 0 && msgCount > 0) {
        document.getElementById('messageList').innerHTML =
          '<div class="empty" id="emptyState"><p>&#x1F4E1;</p><p>Waiting for messages...</p></div>';
        msgCount = 0;
        lastMsgId = null;
        document.getElementById('counter').textContent = '0 messages';
      } else if (data.total > 0 && data.messages[0].id !== lastMsgId) {
        const list = document.getElementById('messageList');
        const empty = document.getElementById('emptyState');
        if (empty) empty.remove();
        list.innerHTML = '';
        msgCount = 0;
        data.messages.forEach(m => {
          list.appendChild(renderMsg(m));
          msgCount++;
        });
        lastMsgId = data.messages[0].id;
        document.getElementById('counter').textContent = msgCount + ' message' + (msgCount !== 1 ? 's' : '');
      }
    } catch(e) {
      dot.classList.remove('connected');
      txt.textContent = 'Error, retrying...';
    }
    await new Promise(r => setTimeout(r, 2000));
  }
}

loadExisting().then(() => poll());
</script>
</body>
</html>"""
    return Response(content=html, media_type="text/html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
