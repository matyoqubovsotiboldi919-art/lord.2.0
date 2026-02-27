const API = window.API_BASE || "";

const $ = (id) => document.getElementById(id);

function toast(title, msg, type="ok") {
  const wrap = $("toasts");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `<div class="t">${escapeHtml(title)}</div><div class="m">${escapeHtml(msg)}</div>`;
  wrap.appendChild(el);
  setTimeout(() => el.remove(), 3200);
}

function escapeHtml(s){
  return String(s ?? "").replace(/[&<>"']/g, (c)=>({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[c]));
}

function setRoute(route){
  // sidebar active
  document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));
  const btn = document.querySelector(`.nav-item[data-route="${route}"]`);
  if (btn) btn.classList.add("active");

  // pages
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  const page = $(`page-${route}`);
  if (page) page.classList.add("active");

  // titles
  const map = {
    dashboard: ["Dashboard", "Live market + wallet"],
    send: ["Send", "Transfer tokens securely"],
    explorer: ["Explorer", "Search tx hash / username"],
    admin: ["Admin", "Users management"],
    auth: ["Auth", "Login / Register"],
  };
  const [t, sub] = map[route] || ["LORD", ""];
  $("pageTitle").textContent = t;
  $("pageSubtitle").textContent = sub;
}

function getToken(){ return localStorage.getItem("token"); }
function setToken(t){ localStorage.setItem("token", t); }
function clearToken(){ localStorage.removeItem("token"); }

async function api(path, {method="GET", body=null, auth=false} = {}) {
  const headers = {"Content-Type":"application/json"};
  if (auth) {
    const t = getToken();
    if (t) headers["Authorization"] = `Bearer ${t}`;
  }
  const res = await fetch(`${API}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null
  });
  let data = null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    try { data = await res.json(); } catch { data = null; }
  } else {
    try { data = await res.text(); } catch { data = null; }
  }
  return {res, data};
}

/* ---------------- Auth + User state ---------------- */
let currentUser = null;

function updateAuthUI(){
  const isAuthed = !!getToken() && !!currentUser;

  $("btnLogout").disabled = !isAuthed;
  $("navAuth").textContent = isAuthed ? "Account" : "Sign in";

  $("whoami").textContent = isAuthed ? currentUser.username : "Guest";
  const bal = isAuthed ? Number(currentUser.balance).toFixed(8) : "0.00000000";
  $("balanceTop").textContent = bal;
  $("walletUser").textContent = isAuthed ? currentUser.username : "Guest";
  $("walletBalance").textContent = bal;
  $("walletRole").textContent = isAuthed ? (currentUser.is_admin ? "ADMIN" : "USER") : "—";

  const navAdmin = $("navAdmin");
  if (isAuthed && currentUser.is_admin) {
    navAdmin.disabled = false;
    navAdmin.title = "";
  } else {
    navAdmin.disabled = true;
    navAdmin.title = "Admin only";
    // if currently on admin page but not admin, bounce
    if ($("page-admin").classList.contains("active")) setRoute("dashboard");
  }
}

async function loadMe(){
  const token = getToken();
  if (!token) {
    currentUser = null;
    updateAuthUI();
    return;
  }

  const {res, data} = await api("/api/v1/users/me", {auth:true});
  if (!res.ok) {
    currentUser = null;
    clearToken();
    updateAuthUI();
    toast("Auth", (data && data.detail) ? data.detail : "Session expired", "err");
    return;
  }
  currentUser = data;
  updateAuthUI();
}

async function doRegister(){
  const username = $("regUsername").value.trim();
  const email = $("regEmail").value.trim();
  const password = $("regPassword").value;

  if (!username || !email || !password) {
    toast("Register", "Fill all fields", "err");
    return;
  }

  const {res, data} = await api("/api/v1/auth/register", {
    method:"POST",
    body:{username, email, password}
  });

  if (res.ok) {
    toast("Register", "Account created. Now login.", "ok");
    $("loginEmail").value = email;
    switchAuthTab("login");
  } else {
    toast("Register", (data && data.detail) ? data.detail : "Failed", "err");
  }
}

async function doLogin(){
  const email = $("loginEmail").value.trim();
  const password = $("loginPassword").value;

  if (!email || !password) {
    toast("Login", "Fill all fields", "err");
    return;
  }

  const {res, data} = await api("/api/v1/auth/login", {
    method:"POST",
    body:{email, password}
  });

  if (!res.ok || !data || !data.access_token) {
    toast("Login", (data && data.detail) ? data.detail : "Login failed", "err");
    return;
  }

  setToken(data.access_token);
  await loadMe();
  toast("Login", "Welcome back", "ok");
  setRoute("dashboard");
}

function doLogout(){
  clearToken();
  currentUser = null;
  updateAuthUI();
  toast("Logout", "Done", "ok");
  setRoute("auth");
}

/* ---------------- Tabs ---------------- */
function switchAuthTab(which){
  document.querySelectorAll(".tab").forEach(t=>t.classList.remove("active"));
  document.querySelectorAll(".tabpane").forEach(p=>p.classList.remove("active"));

  const tab = document.querySelector(`.tab[data-tab="${which}"]`);
  const pane = $(`tab-${which}`);
  if (tab) tab.classList.add("active");
  if (pane) pane.classList.add("active");
}

/* ---------------- Explorer ---------------- */
async function findTx(){
  const tx = $("exTxHash").value.trim();
  if (!tx) return toast("Explorer", "Enter tx hash", "err");
  const {res, data} = await api(`/api/v1/explorer/tx/${encodeURIComponent(tx)}`);
  $("exResult").textContent = JSON.stringify(data, null, 2);
  toast("Explorer", res.ok ? "OK" : "Error", res.ok ? "ok":"err");
}

async function findUser(){
  const u = $("exUsername").value.trim();
  if (!u) return toast("Explorer", "Enter username", "err");
  const {res, data} = await api(`/api/v1/explorer/address/${encodeURIComponent(u)}`);
  $("exResult").textContent = JSON.stringify(data, null, 2);
  toast("Explorer", res.ok ? "OK" : "Error", res.ok ? "ok":"err");
}

async function loadLatest(){
  const {res, data} = await api(`/api/v1/explorer/latest?limit=25`);
  if (!res.ok) return toast("Latest TX", "Failed", "err");

  const list = $("latestTxList");
  list.innerHTML = "";
  const items = (data && data.items) ? data.items : [];
  if (!items.length) {
    list.innerHTML = `<div class="muted">No data</div>`;
    return;
  }
  for (const it of items) {
    const el = document.createElement("div");
    el.className = "tx";
    el.innerHTML = `
      <div class="hash">${escapeHtml(it.tx_hash)}</div>
      <div class="meta">
        <span>from: ${escapeHtml(it.sender_id)}</span>
        <span>to: ${escapeHtml(it.receiver_id)}</span>
        <span>amt: <span class="mono">${Number(it.amount).toFixed(8)}</span></span>
      </div>
    `;
    el.addEventListener("click", ()=>{
      $("exTxHash").value = it.tx_hash;
      setRoute("explorer");
      findTx();
    });
    list.appendChild(el);
  }
  toast("Latest TX", "Loaded", "ok");
}

/* ---------------- Send ---------------- */
function updateSendPreview(){
  const to = $("sendTo").value.trim();
  const amt = parseFloat($("sendAmount").value);
  const wrap = $("sendPreview");

  const authed = !!currentUser;
  const bal = authed ? Number(currentUser.balance) : 0;

  let html = "";
  html += `<div class="box"><div class="muted tiny">Logged</div><div class="mono">${authed ? "YES" : "NO"}</div></div>`;
  html += `<div class="box"><div class="muted tiny">To</div><div class="mono">${escapeHtml(to || "—")}</div></div>`;
  html += `<div class="box"><div class="muted tiny">Amount</div><div class="mono">${isFinite(amt) ? amt.toFixed(8) : "—"}</div></div>`;
  html += `<div class="box"><div class="muted tiny">Your balance</div><div class="mono">${bal.toFixed(8)}</div></div>`;
  if (isFinite(amt) && authed) {
    const after = bal - amt;
    html += `<div class="box"><div class="muted tiny">Balance after</div><div class="mono">${after.toFixed(8)}</div></div>`;
  }
  wrap.innerHTML = html;
}

async function sendTx(){
  if (!currentUser) return toast("Send", "Login required", "err");

  const to_username = $("sendTo").value.trim();
  const amount = parseFloat($("sendAmount").value);

  if (!to_username || !isFinite(amount) || amount <= 0) {
    toast("Send", "Invalid inputs", "err");
    return;
  }

  const {res, data} = await api("/api/v1/tx/send", {
    method:"POST",
    auth:true,
    body:{to_username, amount}
  });

  if (!res.ok) {
    toast("Send", (data && data.detail) ? data.detail : "Failed", "err");
    return;
  }

  toast("Send", `TX sent: ${data.tx_hash}`, "ok");
  await loadMe();
  await loadLatest();
  $("sendAmount").value = "";
  updateSendPreview();
}

/* ---------------- Admin ---------------- */
async function adminReload(){
  if (!currentUser || !currentUser.is_admin) {
    toast("Admin", "Admin only", "err");
    return;
  }

  const {res, data} = await api("/api/v1/admin/users", {auth:true});
  const wrap = $("adminTable");
  wrap.innerHTML = "";

  if (!res.ok) {
    toast("Admin", (data && data.detail) ? data.detail : "Failed", "err");
    wrap.innerHTML = `<div class="muted">Failed</div>`;
    return;
  }

  for (const u of data) {
    const row = document.createElement("div");
    row.className = "userrow";
    const role = u.is_admin ? "ADMIN" : "USER";
    const status = u.is_active ? "ACTIVE" : "FROZEN";

    row.innerHTML = `
      <div class="left">
        <div class="mono"><b>${escapeHtml(u.username)}</b> <span class="tag">${escapeHtml(role)}</span> <span class="tag">${escapeHtml(status)}</span></div>
        <div class="muted tiny">${escapeHtml(u.email)} • id=${u.id} • bal=${Number(u.balance).toFixed(8)}</div>
      </div>
      <div class="right">
        <button class="btn ghost" data-act="freeze">Freeze</button>
        <button class="btn" data-act="unfreeze">Unfreeze</button>
      </div>
    `;

    const freezeBtn = row.querySelector('[data-act="freeze"]');
    const unfreezeBtn = row.querySelector('[data-act="unfreeze"]');

    freezeBtn.disabled = u.is_admin;
    unfreezeBtn.disabled = u.is_admin;

    freezeBtn.addEventListener("click", async ()=>{
      const r = await api(`/api/v1/admin/users/${u.id}/freeze`, {method:"POST", auth:true});
      if (r.res.ok) toast("Admin", "Frozen", "ok"); else toast("Admin", (r.data && r.data.detail) ? r.data.detail : "Failed", "err");
      await adminReload();
    });

    unfreezeBtn.addEventListener("click", async ()=>{
      const r = await api(`/api/v1/admin/users/${u.id}/unfreeze`, {method:"POST", auth:true});
      if (r.res.ok) toast("Admin", "Unfrozen", "ok"); else toast("Admin", (r.data && r.data.detail) ? r.data.detail : "Failed", "err");
      await adminReload();
    });

    wrap.appendChild(row);
  }

  toast("Admin", "Loaded", "ok");
}

/* ---------------- WebSocket + Candlestick chart ---------------- */
let ws = null;
let wsOnline = false;

// candles are {t,o,h,l,c,v}
let candles = [];
let lastPrice = null;

const chart = {
  canvas: null,
  ctx: null,
  w: 0,
  h: 0,
  dpr: 1,
};

function setStatus(text, online){
  $("statusText").textContent = text;
  const pill = $("pillStatus");
  const pulse = pill.querySelector(".pulse");
  pulse.style.background = online ? "rgba(45,255,177,.85)" : "rgba(255,45,111,.85)";
}

function wsUrl(){
  const proto = (location.protocol === "https:") ? "wss" : "ws";
  const host = location.host;
  // API_BASE empty => same host; if API_BASE set, derive host
  if (API && API.startsWith("http")) {
    const u = new URL(API);
    return `${u.protocol === "https:" ? "wss" : "ws"}://${u.host}/ws/market`;
  }
  return `${proto}://${host}/ws/market`;
}

function startWS(){
  stopWS();
  const url = wsUrl();
  ws = new WebSocket(url);

  ws.onopen = () => {
    wsOnline = true;
    $("wsBadge").textContent = "WS: on";
    setStatus("Connected", true);
    toast("WS", "Connected", "ok");
    // keepalive ping from client side
    try { ws.send("hi"); } catch {}
  };

  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      if (msg.type === "snapshot") {
        candles = Array.isArray(msg.candles) ? msg.candles : [];
        lastPrice = msg.price ?? null;
        $("symbol").textContent = msg.symbol || "LORDUSDT";
        $("tf").textContent = `${msg.tf_sec || 60}s`;
        if (lastPrice != null) $("lastPrice").textContent = Number(lastPrice).toFixed(6);
        draw();
        return;
      }
      if (msg.type === "tick") {
        lastPrice = msg.price ?? lastPrice;
        if (lastPrice != null) $("lastPrice").textContent = Number(lastPrice).toFixed(6);

        if (msg.last_candle) {
          const lc = msg.last_candle;
          // merge into candles
          if (!candles.length || candles[candles.length - 1].t !== lc.t) {
            candles.push(lc);
            if (candles.length > 500) candles = candles.slice(-500);
          } else {
            candles[candles.length - 1] = lc;
          }
          $("candleOHLC").textContent = `${Number(lc.o).toFixed(4)} / ${Number(lc.h).toFixed(4)} / ${Number(lc.l).toFixed(4)} / ${Number(lc.c).toFixed(4)}`;
          draw();
        }
        // ping keepalive
        try { ws.send("p"); } catch {}
      }
    } catch {}
  };

  ws.onclose = () => {
    wsOnline = false;
    $("wsBadge").textContent = "WS: off";
    setStatus("Disconnected", false);
  };

  ws.onerror = () => {
    wsOnline = false;
    $("wsBadge").textContent = "WS: off";
    setStatus("Disconnected", false);
  };
}

function stopWS(){
  try { ws?.close(); } catch {}
  ws = null;
  wsOnline = false;
}

function initCanvas(){
  chart.canvas = $("chart");
  chart.ctx = chart.canvas.getContext("2d");

  const resize = () => {
    const rect = chart.canvas.getBoundingClientRect();
    chart.dpr = window.devicePixelRatio || 1;
    chart.w = Math.max(300, Math.floor(rect.width));
    chart.h = Math.max(240, Math.floor(rect.height));
    chart.canvas.width = Math.floor(chart.w * chart.dpr);
    chart.canvas.height = Math.floor(chart.h * chart.dpr);
    chart.ctx.setTransform(chart.dpr, 0, 0, chart.dpr, 0, 0);
    draw();
  };

  window.addEventListener("resize", resize);
  resize();
}

function draw(){
  const ctx = chart.ctx;
  if (!ctx) return;

  const W = chart.w, H = chart.h;
  ctx.clearRect(0,0,W,H);

  // grid
  ctx.globalAlpha = 0.65;
  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.lineWidth = 1;
  for (let x=0; x<=W; x+=80) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,H); ctx.stroke(); }
  for (let y=0; y<=H; y+=60) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(W,y); ctx.stroke(); }
  ctx.globalAlpha = 1;

  const pad = 18;
  const plotW = W - pad*2;
  const plotH = H - pad*2;

  const view = candles.slice(-90);
  if (!view.length) {
    ctx.fillStyle = "rgba(255,255,255,0.65)";
    ctx.font = "14px Poppins";
    ctx.fillText("Waiting for candles…", pad, pad+18);
    return;
  }

  // min/max
  let min = Infinity, max = -Infinity;
  for (const c of view) {
    const lo = Number(c.l), hi = Number(c.h);
    if (lo < min) min = lo;
    if (hi > max) max = hi;
  }
  if (min === max) { min -= 1; max += 1; }
  const range = max - min;

  const xStep = plotW / view.length;
  const bodyW = Math.max(4, Math.min(10, xStep * 0.55));

  const yOf = (p) => pad + (max - p) / range * plotH;

  // axis labels
  ctx.fillStyle = "rgba(255,255,255,0.55)";
  ctx.font = "12px " + getComputedStyle(document.body).fontFamily;
  ctx.fillText(max.toFixed(4), pad, pad - 4);
  ctx.fillText(min.toFixed(4), pad, pad + plotH + 14);

  for (let i=0; i<view.length; i++) {
    const c = view[i];
    const o = Number(c.o), h = Number(c.h), l = Number(c.l), cl = Number(c.c);
    const up = cl >= o;

    const x = pad + i * xStep + xStep/2;

    // wick
    ctx.strokeStyle = up ? "rgba(45,255,177,0.85)" : "rgba(255,45,111,0.85)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x, yOf(h));
    ctx.lineTo(x, yOf(l));
    ctx.stroke();

    // body
    const y1 = yOf(o);
    const y2 = yOf(cl);
    const top = Math.min(y1, y2);
    const bot = Math.max(y1, y2);
    const bodyH = Math.max(2, bot - top);

    ctx.fillStyle = up ? "rgba(45,255,177,0.35)" : "rgba(255,45,111,0.35)";
    ctx.strokeStyle = up ? "rgba(45,255,177,0.90)" : "rgba(255,45,111,0.90)";
    ctx.lineWidth = 1.5;

    ctx.beginPath();
    ctx.roundRect(x - bodyW/2, top, bodyW, bodyH, 4);
    ctx.fill();
    ctx.stroke();
  }

  // last price line
  if (lastPrice != null) {
    const y = yOf(Number(lastPrice));
    ctx.strokeStyle = "rgba(0,229,255,0.35)";
    ctx.lineWidth = 1;
    ctx.setLineDash([6,6]);
    ctx.beginPath();
    ctx.moveTo(pad, y);
    ctx.lineTo(pad+plotW, y);
    ctx.stroke();
    ctx.setLineDash([]);
  }
}

/* ---------------- init ---------------- */
function bindNav(){
  document.querySelectorAll(".nav-item[data-route]").forEach(btn=>{
    btn.addEventListener("click", ()=>{
      const r = btn.getAttribute("data-route");
      if (btn.disabled) return toast("Access", "Not allowed", "err");
      setRoute(r);
      if (r === "admin") adminReload();
    });
  });
}

function bindAuth(){
  document.querySelectorAll(".tab").forEach(t=>{
    t.addEventListener("click", ()=> switchAuthTab(t.dataset.tab));
  });
  $("btnLogin").addEventListener("click", doLogin);
  $("btnRegister").addEventListener("click", doRegister);
  $("btnLogout").addEventListener("click", doLogout);
  $("btnRefreshMe").addEventListener("click", async ()=>{ await loadMe(); toast("Account", "Refreshed", "ok"); });
}

function bindExplorer(){
  $("btnFindTx").addEventListener("click", findTx);
  $("btnFindUser").addEventListener("click", findUser);
  $("btnLoadLatest").addEventListener("click", loadLatest);
}

function bindSend(){
  $("sendTo").addEventListener("input", updateSendPreview);
  $("sendAmount").addEventListener("input", updateSendPreview);
  $("btnSend").addEventListener("click", sendTx);
}

function bindAdmin(){
  $("btnAdminReload").addEventListener("click", adminReload);
}

/* polyfill for roundRect (older browsers) */
if (!CanvasRenderingContext2D.prototype.roundRect) {
  CanvasRenderingContext2D.prototype.roundRect = function (x, y, w, h, r) {
    const rr = Math.min(r, w/2, h/2);
    this.beginPath();
    this.moveTo(x+rr, y);
    this.arcTo(x+w, y, x+w, y+h, rr);
    this.arcTo(x+w, y+h, x, y+h, rr);
    this.arcTo(x, y+h, x, y, rr);
    this.arcTo(x, y, x+w, y, rr);
    this.closePath();
    return this;
  };
}

window.addEventListener("DOMContentLoaded", async ()=>{
  // fx grid fill (optional extra nodes)
  const grid = $("fxGrid");
  // no extra heavy nodes; css handles grid

  bindNav();
  bindAuth();
  bindExplorer();
  bindSend();
  bindAdmin();

  initCanvas();
  setStatus("Disconnected", false);
  setRoute("dashboard");

  await loadMe();
  updateSendPreview();

  // start ws always for market
  startWS();
  // also load latest tx
  loadLatest();
});