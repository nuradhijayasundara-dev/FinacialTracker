const $ = (id) => document.getElementById(id);
let token = localStorage.getItem("token");
let catChart, monthChart;

async function api(path, options = {}) {
  const res = await fetch("/api" + path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: "Bearer " + token } : {}),
    },
  });
  if (res.status === 401 && token) { logout(); throw new Error("Session expired"); }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = Array.isArray(err.detail) ? err.detail[0].msg : err.detail;
    throw new Error(detail || "Request failed");
  }
  return res.status === 204 ? null : res.json();
}

const money = (n) => n.toLocaleString(undefined, { style: "currency", currency: "USD" });

function showApp(on) {
  $("auth").hidden = on;
  $("app").hidden = !on;
  if (on) { $("date").valueAsDate = new Date(); refresh(); }
}

function logout() {
  token = null;
  localStorage.removeItem("token");
  showApp(false);
}

$("auth-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const mode = e.submitter.dataset.mode;
  try {
    const data = await api("/" + mode, {
      method: "POST",
      body: JSON.stringify({ username: $("username").value.trim(), password: $("password").value }),
    });
    token = data.access_token;
    localStorage.setItem("token", token);
    $("auth-error").textContent = "";
    showApp(true);
  } catch (err) { $("auth-error").textContent = err.message; }
});

$("logout").addEventListener("click", logout);

$("tx-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  await api("/transactions", {
    method: "POST",
    body: JSON.stringify({
      kind: $("kind").value,
      amount: parseFloat($("amount").value),
      category: $("category").value.trim(),
      description: $("description").value.trim(),
      date: $("date").value,
    }),
  });
  $("amount").value = ""; $("description").value = "";
  refresh();
});

async function removeTx(id) {
  await api("/transactions/" + id, { method: "DELETE" });
  refresh();
}

function drawChart(existing, canvasId, config) {
  if (existing) existing.destroy();
  return new Chart($(canvasId), config);
}

async function refresh() {
  const [txs, sum] = await Promise.all([api("/transactions"), api("/summary")]);

  $("s-income").textContent = money(sum.income);
  $("s-expense").textContent = money(sum.expense);
  $("s-balance").textContent = money(sum.balance);
  $("s-balance").className = sum.balance >= 0 ? "pos" : "neg";

  const body = $("tx-body");
  body.replaceChildren();
  for (const t of txs) {
    const tr = document.createElement("tr");
    for (const c of [t.date, t.category, t.description]) {
      const td = document.createElement("td");
      td.textContent = c;
      tr.append(td);
    }
    const amt = document.createElement("td");
    amt.className = "r " + (t.kind === "income" ? "pos" : "neg");
    amt.textContent = (t.kind === "income" ? "+" : "−") + money(t.amount);
    const act = document.createElement("td");
    const btn = document.createElement("button");
    btn.className = "del"; btn.textContent = "✕"; btn.title = "Delete";
    btn.onclick = () => removeTx(t.id);
    act.append(btn);
    tr.append(amt, act);
    body.append(tr);
  }
  $("empty").hidden = txs.length > 0;

  catChart = drawChart(catChart, "cat-chart", {
    type: "doughnut",
    data: { labels: Object.keys(sum.by_category), datasets: [{ data: Object.values(sum.by_category) }] },
  });
  const months = Object.keys(sum.by_month);
  monthChart = drawChart(monthChart, "month-chart", {
    type: "bar",
    data: {
      labels: months,
      datasets: [
        { label: "Income", data: months.map((m) => sum.by_month[m].income), backgroundColor: "#16a34a" },
        { label: "Expenses", data: months.map((m) => sum.by_month[m].expense), backgroundColor: "#dc2626" },
      ],
    },
  });
}

showApp(!!token);
