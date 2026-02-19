"""Max Bot API Emulator.

Emulates the Max messenger platform API endpoints used by the crossposter backend.
Validates bot tokens and chat IDs like the real Max API.
Stores received messages in memory and provides a real-time web UI to view them.

Configure valid tokens and chat IDs via the /emulator/config endpoints or the dashboard UI.
"""

import asyncio
import base64
import json
import logging
import os
import time
import uuid
from collections import deque
from datetime import datetime, timezone

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="Max Bot API Emulator")

# In-memory storage
messages: deque[dict] = deque(maxlen=200)
uploads: dict[str, dict] = {}
sse_clients: list[asyncio.Queue] = []

# Registry of valid bot tokens and chat IDs.
# Each token maps to a bot info dict. Each chat_id is a known channel.
# Pre-seed from env vars if provided (comma-separated).
_env_tokens = os.environ.get("EMULATOR_BOT_TOKENS", "")
_env_chats = os.environ.get("EMULATOR_CHAT_IDS", "")

bot_tokens: dict[str, dict] = {}
for _t in (t.strip() for t in _env_tokens.split(",") if t.strip()):
    bot_tokens[_t] = {
        "user_id": abs(hash(_t)) % 10**8,
        "name": f"Bot {_t[:8]}...",
        "username": f"bot_{_t[:6]}",
    }

valid_chat_ids: set[int] = set()
for _c in (c.strip() for c in _env_chats.split(",") if c.strip()):
    try:
        valid_chat_ids.add(int(_c))
    except ValueError:
        pass


def _error_response(code: str, status: int, message: str) -> JSONResponse:
    """Return a Max-API-style error response."""
    return JSONResponse(
        status_code=status,
        content={"code": code, "message": message},
    )


def get_token(request: Request) -> str | None:
    """Extract token from Authorization header (the only supported method)."""
    auth = request.headers.get("Authorization")
    if auth:
        return auth.strip()
    return None


def validate_token(request: Request) -> tuple[str, dict] | JSONResponse:
    """Validate the Authorization token. Returns (token, bot_info) or error response."""
    token = get_token(request)
    if not token:
        return _error_response(
            "unauthorized", 401, "Authorization header is required"
        )
    # If no tokens are registered, accept any token (open mode)
    if bot_tokens:
        bot_info = bot_tokens.get(token)
        if not bot_info:
            return _error_response(
                "unauthorized", 401, "Invalid bot token"
            )
        return token, bot_info
    # Open mode — generate bot info from token
    return token, {
        "user_id": abs(hash(token)) % 10**8,
        "name": "Bot",
        "username": "bot",
    }


def validate_chat_id(chat_id: int | None) -> JSONResponse | None:
    """Validate the chat_id parameter. Returns error response or None if valid."""
    if chat_id is None:
        return _error_response(
            "bad.request", 400, "chat_id query parameter is required"
        )
    # If no chat IDs are registered, accept any (open mode)
    if valid_chat_ids and chat_id not in valid_chat_ids:
        return _error_response(
            "not.found", 404, f"Chat not found: {chat_id}"
        )
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
async def get_bot_info(request: Request):
    """Return bot info. Requires valid Authorization token."""
    result = validate_token(request)
    if isinstance(result, JSONResponse):
        return result
    token, bot_info = result
    return {
        "user_id": bot_info["user_id"],
        "name": bot_info["name"],
        "username": bot_info["username"],
        "is_bot": True,
        "last_activity_time": int(time.time() * 1000),
    }


@app.post("/messages")
async def send_message(
    request: Request,
    chat_id: int | None = Query(None),
):
    """Receive a message (text or with attachments). Validates token and chat_id."""
    # Validate token
    token_result = validate_token(request)
    if isinstance(token_result, JSONResponse):
        return token_result
    token, bot_info = token_result

    # Validate chat_id
    chat_err = validate_chat_id(chat_id)
    if chat_err:
        return chat_err

    # Validate request body
    try:
        body = await request.json()
    except Exception:
        return _error_response("bad.request", 400, "Invalid JSON body")

    if not body.get("text") and not body.get("attachments"):
        return _error_response(
            "bad.request", 400, "Message must contain text or attachments"
        )

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
        "status": "ok",
    }
    messages.appendleft(stored)
    await broadcast_event({"type": "message", "data": stored})

    return {
        "message": {
            "body": body,
            "link": None,
            "sender": {
                "user_id": bot_info["user_id"],
                "name": bot_info["name"],
            },
            "recipient": {"chat_id": chat_id, "chat_type": "channel"},
            "timestamp": int(time.time() * 1000),
            "stat": {"views": 0},
        },
        "message_id": msg_id,
    }


@app.post("/uploads")
async def upload_file(
    request: Request,
    chat_id: int | None = Query(None),
    type: str | None = Query(None),
):
    """Receive a file upload. Validates token and chat_id."""
    # Validate token
    token_result = validate_token(request)
    if isinstance(token_result, JSONResponse):
        return token_result
    token, bot_info = token_result

    # Validate chat_id
    chat_err = validate_chat_id(chat_id)
    if chat_err:
        return chat_err

    raw = await request.body()
    if not raw:
        return _error_response("bad.request", 400, "Empty upload body")

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
        "token": (token or "")[:8] + "...",
        "chat_id": chat_id,
        "text": f"[Upload: {type or 'file'}, {len(raw)} bytes, {content_type}]",
        "attachments": [],
        "photo_thumbnail": thumbnail,
        "raw_body": {"upload_type": type, "size": len(raw)},
        "status": "ok",
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


@app.get("/emulator/config")
async def get_config():
    """Return current emulator configuration (registered tokens and chat IDs)."""
    return {
        "tokens": [
            {"token": t, "masked": t[:8] + "..." + t[-4:] if len(t) > 12 else t, **info}
            for t, info in bot_tokens.items()
        ],
        "chat_ids": sorted(valid_chat_ids),
    }


@app.post("/emulator/config/token")
async def add_token(request: Request):
    """Register a new bot token."""
    body = await request.json()
    token = body.get("token", "").strip()
    name = body.get("name", "").strip()
    if not token:
        return _error_response("bad.request", 400, "token is required")
    bot_tokens[token] = {
        "user_id": abs(hash(token)) % 10**8,
        "name": name or f"Bot {token[:8]}...",
        "username": f"bot_{token[:6]}",
    }
    await broadcast_event({"type": "config_changed"})
    return {"status": "ok", "total_tokens": len(bot_tokens)}


@app.delete("/emulator/config/token")
async def remove_token(request: Request):
    """Remove a registered bot token."""
    body = await request.json()
    token = body.get("token", "").strip()
    bot_tokens.pop(token, None)
    await broadcast_event({"type": "config_changed"})
    return {"status": "ok", "total_tokens": len(bot_tokens)}


@app.post("/emulator/config/chat")
async def add_chat_id(request: Request):
    """Register a valid chat ID."""
    body = await request.json()
    chat_id = body.get("chat_id")
    if chat_id is None:
        return _error_response("bad.request", 400, "chat_id is required")
    try:
        valid_chat_ids.add(int(chat_id))
    except (ValueError, TypeError):
        return _error_response("bad.request", 400, "chat_id must be an integer")
    await broadcast_event({"type": "config_changed"})
    return {"status": "ok", "total_chat_ids": len(valid_chat_ids)}


@app.delete("/emulator/config/chat")
async def remove_chat_id(request: Request):
    """Remove a registered chat ID."""
    body = await request.json()
    chat_id = body.get("chat_id")
    try:
        valid_chat_ids.discard(int(chat_id))
    except (ValueError, TypeError):
        pass
    await broadcast_event({"type": "config_changed"})
    return {"status": "ok", "total_chat_ids": len(valid_chat_ids)}


# ── Web UI ─────────────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Real-time dashboard showing received messages and emulator config."""
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
    --yellow: #fdcb6e;
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
  .btn.active { border-color: var(--accent); color: var(--accent); background: rgba(108,92,231,0.1); }
  .counter {
    font-size: 13px;
    color: var(--muted);
    padding: 0 12px;
  }

  /* Tabs */
  .tabs {
    display: flex;
    gap: 0;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
    padding: 0 24px;
  }
  .tab {
    padding: 10px 20px;
    font-size: 13px;
    font-family: inherit;
    color: var(--muted);
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    cursor: pointer;
    transition: all 0.15s;
  }
  .tab:hover { color: var(--text); }
  .tab.active { color: var(--accent); border-bottom-color: var(--accent); }

  .tab-content { display: none; }
  .tab-content.active { display: block; }

  /* Messages tab */
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
  .msg.error {
    border-color: var(--red);
    background: rgba(225,112,85,0.05);
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
  .msg-status-ok { color: var(--green); }
  .msg-status-err { color: var(--red); }
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

  /* Config tab */
  .config-section {
    padding: 24px;
  }
  .config-section h2 {
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 16px;
    color: var(--text);
  }
  .config-section h2 span {
    color: var(--muted);
    font-weight: 400;
    font-size: 12px;
    margin-left: 8px;
  }
  .config-row {
    display: flex;
    gap: 8px;
    margin-bottom: 12px;
  }
  .config-input {
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
    font-family: inherit;
    flex: 1;
  }
  .config-input::placeholder { color: var(--muted); }
  .config-input:focus { outline: none; border-color: var(--accent); }
  .config-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 24px;
  }
  .config-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 13px;
  }
  .config-item .label { color: var(--text); }
  .config-item .detail { color: var(--muted); font-size: 11px; }
  .config-item .remove-btn {
    background: none;
    border: none;
    color: var(--muted);
    cursor: pointer;
    font-size: 16px;
    padding: 0 4px;
    font-family: inherit;
  }
  .config-item .remove-btn:hover { color: var(--red); }
  .mode-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
  }
  .mode-badge.open { background: rgba(253,203,110,0.15); color: var(--yellow); }
  .mode-badge.strict { background: rgba(0,184,148,0.15); color: var(--green); }
  .info-text {
    color: var(--muted);
    font-size: 12px;
    margin-bottom: 16px;
    line-height: 1.5;
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

<div class="tabs">
  <button class="tab active" onclick="switchTab('messages')">Messages</button>
  <button class="tab" onclick="switchTab('config')">Config</button>
</div>

<div class="tab-content active" id="tab-messages">
  <div class="messages" id="messageList">
    <div class="empty" id="emptyState">
      <p>&#x1F4E1;</p>
      <p>Waiting for messages...</p>
      <p style="margin-top:8px;font-size:12px;">
        Send requests to this server's <code>/messages</code> or <code>/uploads</code> endpoints
      </p>
    </div>
  </div>
</div>

<div class="tab-content" id="tab-config">
  <div class="config-section">
    <h2>Bot Tokens <span id="tokenMode"></span></h2>
    <p class="info-text">
      Register valid bot tokens. When no tokens are registered, any token is accepted (open mode).
      When at least one token is registered, only registered tokens are accepted (strict mode).
    </p>
    <div class="config-row">
      <input class="config-input" id="newToken" placeholder="Bot token (e.g. AAHdqTcv...)" style="flex:2;">
      <input class="config-input" id="newTokenName" placeholder="Bot name (optional)" style="flex:1;">
      <button class="btn" onclick="addToken()">Add</button>
    </div>
    <div class="config-list" id="tokenList"></div>

    <h2>Chat IDs <span id="chatMode"></span></h2>
    <p class="info-text">
      Register valid chat/channel IDs. When no IDs are registered, any chat_id is accepted (open mode).
      When at least one ID is registered, only registered IDs are accepted (strict mode).
    </p>
    <div class="config-row">
      <input class="config-input" id="newChatId" placeholder="Chat ID (e.g. 123456)" type="number">
      <button class="btn" onclick="addChatId()">Add</button>
    </div>
    <div class="config-list" id="chatList"></div>
  </div>
</div>

<script>
let msgCount = 0;

/* ── Tab switching ── */
function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.querySelector('.tab[onclick*="' + name + '"]').classList.add('active');
  if (name === 'config') loadConfig();
}

/* ── Config management ── */
async function loadConfig() {
  try {
    const res = await fetch('/emulator/config');
    const data = await res.json();
    renderTokens(data.tokens);
    renderChatIds(data.chat_ids);
  } catch(e) {
    console.error('Failed to load config:', e);
  }
}

function renderTokens(tokens) {
  const list = document.getElementById('tokenList');
  const mode = document.getElementById('tokenMode');
  if (tokens.length === 0) {
    list.innerHTML = '<div style="color:var(--muted);font-size:12px;padding:8px;">No tokens registered — accepting any token</div>';
    mode.innerHTML = '<span class="mode-badge open">OPEN</span>';
  } else {
    mode.innerHTML = '<span class="mode-badge strict">STRICT</span>';
    list.innerHTML = tokens.map(t =>
      '<div class="config-item">' +
        '<div><span class="label">' + escapeHtml(t.masked) + '</span>' +
        '<span class="detail" style="margin-left:12px;">' + escapeHtml(t.name) + '</span></div>' +
        '<button class="remove-btn" onclick="removeToken(\'' + escapeAttr(t.token) + '\')">&times;</button>' +
      '</div>'
    ).join('');
  }
}

function renderChatIds(chatIds) {
  const list = document.getElementById('chatList');
  const mode = document.getElementById('chatMode');
  if (chatIds.length === 0) {
    list.innerHTML = '<div style="color:var(--muted);font-size:12px;padding:8px;">No chat IDs registered — accepting any chat_id</div>';
    mode.innerHTML = '<span class="mode-badge open">OPEN</span>';
  } else {
    mode.innerHTML = '<span class="mode-badge strict">STRICT</span>';
    list.innerHTML = chatIds.map(id =>
      '<div class="config-item">' +
        '<span class="label">' + id + '</span>' +
        '<button class="remove-btn" onclick="removeChatId(' + id + ')">&times;</button>' +
      '</div>'
    ).join('');
  }
}

async function addToken() {
  const tokenEl = document.getElementById('newToken');
  const nameEl = document.getElementById('newTokenName');
  const token = tokenEl.value.trim();
  if (!token) return;
  await fetch('/emulator/config/token', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({token: token, name: nameEl.value.trim()})
  });
  tokenEl.value = '';
  nameEl.value = '';
  loadConfig();
}

async function removeToken(token) {
  await fetch('/emulator/config/token', {
    method: 'DELETE',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({token: token})
  });
  loadConfig();
}

async function addChatId() {
  const el = document.getElementById('newChatId');
  const chatId = parseInt(el.value);
  if (isNaN(chatId)) return;
  await fetch('/emulator/config/chat', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({chat_id: chatId})
  });
  el.value = '';
  loadConfig();
}

async function removeChatId(chatId) {
  await fetch('/emulator/config/chat', {
    method: 'DELETE',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({chat_id: chatId})
  });
  loadConfig();
}

/* ── Messages ── */
function formatTime(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString('en-GB', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
}

function renderMsg(msg) {
  const el = document.createElement('div');
  el.className = 'msg' + (msg.status === 'error' ? ' error' : '');
  const rawId = 'raw-' + msg.id;

  let photoHtml = '';
  if (msg.photo_thumbnail) {
    photoHtml = '<img class="msg-photo" src="' + msg.photo_thumbnail + '" alt="uploaded photo">';
  }

  let attachInfo = '';
  if (msg.attachments && msg.attachments.length > 0) {
    attachInfo = ' | ' + msg.attachments.length + ' attachment(s)';
  }

  const statusClass = msg.status === 'error' ? 'msg-status-err' : 'msg-status-ok';
  const statusLabel = msg.status === 'error' ? 'ERR' : 'OK';

  el.innerHTML =
    '<div class="msg-header">' +
      '<span class="msg-id">#' + msg.id + '</span>' +
      '<span class="' + statusClass + '">' + statusLabel + '</span>' +
      '<span class="msg-chat">chat:' + (msg.chat_id || '?') + '</span>' +
      '<span>token:' + (msg.token || '?') + '</span>' +
      attachInfo +
      '<span class="msg-time">' + formatTime(msg.timestamp) + '</span>' +
    '</div>' +
    '<div class="msg-body">' + escapeHtml(msg.text || '(no text)') + '</div>' +
    photoHtml +
    '<button class="toggle-raw" onclick="toggleRaw(\'' + rawId + '\')">show raw</button>' +
    '<div class="msg-raw" id="' + rawId + '">' + escapeHtml(JSON.stringify(msg.raw_body, null, 2)) + '</div>';

  return el;
}

function escapeHtml(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function escapeAttr(s) {
  return s.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
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
    '<div class="empty" id="emptyState"><p>&#x1F4E1;</p><p>Waiting for messages...</p></div>';
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
