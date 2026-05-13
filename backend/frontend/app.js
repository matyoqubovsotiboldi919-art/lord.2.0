(() => {
  const API = ""; // same-origin on Render

  const $ = (id) => document.getElementById(id);
  const toast = $("toast");

  const authCard = $("authCard");
  const dashCard = $("dashCard");

  const tabLogin = $("tabLogin");
  const tabRegister = $("tabRegister");

  const loginForm = $("loginForm");
  const registerForm = $("registerForm");

  const authHint = $("authHint");
  const sendHint = $("sendHint");

  const btnLogout = $("btnLogout");

  const meLine = $("meLine");
  const statusPill = $("statusPill");
  const balanceEl = $("balance");
  const addressEl = $("address");
  const copyAddress = $("copyAddress");

  const historyBody = $("historyBody");

  const sendForm = $("sendForm");
  const recvAddress = $("recvAddress");
  const amount = $("amount");

  // Explorer
  const explorerForm = $("explorerForm");
  const explorerAddress = $("explorerAddress");
  const explorerOut = $("explorerOut");
  const explorerTxBody = $("explorerTxBody");

  // Admin
  const adminBlock = $("adminBlock");
  const adminOut = $("adminOut");

  const tokenKey = "lord_token";

  const showToast = (msg) => {
    toast.textContent = msg;
    toast.classList.remove("hidden");

    clearTimeout(showToast._t);

    showToast._t = setTimeout(() => {
      toast.classList.add("hidden");
    }, 1800);
  };

  const setAuthMode = (mode) => {
    if (mode === "login") {
      tabLogin.classList.add("active");
      tabRegister.classList.remove("active");

      loginForm.classList.remove("hidden");
      registerForm.classList.add("hidden");

      authHint.textContent = "";
    } else {
      tabRegister.classList.add("active");
      tabLogin.classList.remove("active");

      registerForm.classList.remove("hidden");
      loginForm.classList.add("hidden");

      authHint.textContent = "";
    }
  };

  tabLogin.onclick = () => setAuthMode("login");
  tabRegister.onclick = () => setAuthMode("register");

  const getToken = () => sessionStorage.getItem(tokenKey);

  const setToken = (t) => {
    sessionStorage.setItem(tokenKey, t);
  };

  const clearToken = () => {
    sessionStorage.removeItem(tokenKey);
  };

  async function api(path, opts = {}) {
    const headers = opts.headers || {};

    headers["Content-Type"] = "application/json";

    const t = getToken();

    if (t) {
      headers["Authorization"] = `Bearer ${t}`;
    }

    const res = await fetch(`${API}${path}`, {
      ...opts,
      headers,
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const msg = data.detail || `HTTP ${res.status}`;
      throw new Error(msg);
    }

    return data;
  }

  function showAuth() {
    authCard.classList.remove("hidden");
    dashCard.classList.add("hidden");
    btnLogout.classList.add("hidden");
  }

  function showDash() {
    authCard.classList.add("hidden");
    dashCard.classList.remove("hidden");
    btnLogout.classList.remove("hidden");
  }

  async function loadMe() {
    const me = await api("/api/v1/users/me");

    meLine.textContent = `ID: ${me.public_id} • ${me.email}`;
    statusPill.textContent = me.status;

    balanceEl.textContent = me.balance_usdt;
    addressEl.textContent = me.address;

    if (me.role === "ADMIN") {
      adminBlock.classList.remove("hidden");
    } else {
      adminBlock.classList.add("hidden");
    }

    return me;
  }

  function txRowHtml(r) {
    return `
      <div class="mono">${r.from_address}</div>
      <div class="mono">${r.to_address}</div>
      <div>${r.amount_usdt}</div>
      <div class="mono">${new Date(r.created_at).toLocaleString()}</div>
      <div>${r.status}</div>
      <div class="mono">${r.tx_hash}</div>
    `;
  }

  async function loadHistory() {
    const rows = await api("/api/v1/tx/history");

    historyBody.innerHTML = "";

    if (!rows.length) {
      historyBody.innerHTML = `
        <div class="empty">
          No transactions yet
        </div>
      `;
      return;
    }

    rows.forEach((r) => {
      const row = document.createElement("div");

      row.className = "row txTable";

      row.innerHTML = txRowHtml(r);

      historyBody.appendChild(row);
    });
  }

  loginForm.onsubmit = async (e) => {
    e.preventDefault();

    authHint.textContent = "Logging in…";

    try {
      const email = $("loginEmail").value.trim();
      const password = $("loginPassword").value;

      const out = await api("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
        }),
      });

      setToken(out.access_token);

      showDash();

      await boot();

      showToast("Logged in");
    } catch (err) {
      authHint.textContent = err.message;
      showToast(err.message);
    }
  };

  registerForm.onsubmit = async (e) => {
    e.preventDefault();

    authHint.textContent = "Creating account…";

    try {
      const email = $("regEmail").value.trim();
      const password = $("regPassword").value;

      await api("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
        }),
      });

      authHint.textContent = "Account created. Now login.";

      setAuthMode("login");

      showToast("Registered");
    } catch (err) {
      authHint.textContent = err.message;
      showToast(err.message);
    }
  };

  btnLogout.onclick = () => {
    clearToken();

    showAuth();

    showToast("Logged out");
  };

  copyAddress.onclick = async () => {
    try {
      await navigator.clipboard.writeText(addressEl.textContent);

      showToast("Address copied");
    } catch {
      showToast("Copy failed");
    }
  };

  sendForm.onsubmit = async (e) => {
    e.preventDefault();

    sendHint.textContent = "Sending…";

    try {
      const receiver_address = recvAddress.value.trim();
      const amount_usdt = amount.value.trim();

      const out = await api("/api/v1/tx/transfer", {
        method: "POST",
        body: JSON.stringify({
          receiver_address,
          amount_usdt,
        }),
      });

      sendHint.textContent = `Sent. TX: ${out.tx_hash}`;

      recvAddress.value = "";
      amount.value = "";

      await boot();

      showToast("Transfer done");
    } catch (err) {
      sendHint.textContent = err.message;
      showToast(err.message);
    }
  };

  // Explorer address scan
  explorerForm.onsubmit = async (e) => {
    e.preventDefault();

    explorerOut.innerHTML = "Checking…";
    explorerTxBody.innerHTML = "";

    try {
      const address = explorerAddress.value.trim();

      const out = await api(
        `/api/v1/explorer/address/${encodeURIComponent(address)}`
      );

      explorerOut.innerHTML = `
        <div class="scanGrid">

          <div class="scanItem">
            <div class="miniLabel">Address</div>
            <div class="mono scanValue">${out.address}</div>
          </div>

          <div class="scanItem">
            <div class="miniLabel">Balance</div>
            <div class="scanValue">${out.balance_usdt} USDT</div>
          </div>

          <div class="scanItem">
            <div class="miniLabel">Last active</div>
            <div class="scanValue">
              ${
                out.last_active
                  ? new Date(out.last_active).toLocaleString()
                  : "No activity"
              }
            </div>
          </div>

          <div class="scanItem">
            <div class="miniLabel">Status</div>
            <div class="scanValue">
              ${out.exists ? "Address found" : "Address not found"}
            </div>
          </div>

        </div>
      `;

      if (!out.transactions.length) {
        explorerTxBody.innerHTML = `
          <div class="empty">
            No transactions found for this address
          </div>
        `;
        return;
      }

      out.transactions.forEach((r) => {
        const row = document.createElement("div");

        row.className = "row txTable";

        row.innerHTML = txRowHtml(r);

        explorerTxBody.appendChild(row);
      });
    } catch (err) {
      explorerOut.textContent = err.message;
      showToast(err.message);
    }
  };

  // Admin
  document.querySelectorAll(".admin-tabs button").forEach((b) => {
    b.onclick = async () => {
      try {
        const k = b.getAttribute("data-a");

        adminOut.textContent = "Loading…";

        if (k === "users") {
          adminOut.textContent = JSON.stringify(
            await api("/api/v1/admin/users"),
            null,
            2
          );
        }

        if (k === "txs") {
          adminOut.textContent = JSON.stringify(
            await api("/api/v1/admin/transactions"),
            null,
            2
          );
        }

        if (k === "logs") {
          adminOut.textContent = JSON.stringify(
            await api("/api/v1/admin/logs"),
            null,
            2
          );
        }
      } catch (err) {
        adminOut.textContent = err.message;
      }
    };
  });

  async function boot() {
    await loadMe();
    await loadHistory();
  }

  // Initial
  (async () => {
    const t = getToken();

    if (!t) {
      showAuth();
      return;
    }

    try {
      showDash();

      await boot();
    } catch (err) {
      clearToken();

      showAuth();

      showToast("Session expired. Login again.");
    }
  })();
})();