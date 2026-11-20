const statusEl = document.getElementById("save-status");
const runtimeEl = document.getElementById("runtime-status");
const controlsEl = document.getElementById("controls");
const resetBtn = document.getElementById("btn-reset");

let specs = {};
let values = {};
let saveTimer = null;

function setStatus(text, kind = "") {
  statusEl.textContent = text;
  statusEl.className = "status" + (kind ? ` status--${kind}` : "");
}

function formatValue(key, val) {
  const spec = specs[key];
  if (spec.type === "float") {
    const step = spec.step || 0.01;
    const decimals = String(step).includes(".")
      ? String(step).split(".")[1].length
      : 0;
    return Number(val).toFixed(decimals);
  }
  if (spec.type === "int") return String(Math.round(Number(val)));
  return String(val);
}

function buildControls() {
  controlsEl.innerHTML = "";
  const byGroup = {};
  for (const [key, spec] of Object.entries(specs)) {
    const group = spec.group || "Other";
    if (!byGroup[group]) byGroup[group] = [];
    byGroup[group].push([key, spec]);
  }

  for (const [group, entries] of Object.entries(byGroup)) {
    const panel = document.createElement("section");
    panel.className = "panel";
    panel.innerHTML = `<h2 class="panel__title">${group}</h2>`;
    const inner = document.createElement("div");

    for (const [key, spec] of entries) {
      const field = document.createElement("div");
      field.className = "field" + (spec.live === false ? " field--restart" : "");

      const head = document.createElement("div");
      head.className = "field__head";
      head.innerHTML = `
        <span class="field__label">${spec.label}</span>
        <span class="field__value" data-key="${key}">${formatValue(key, values[key])}</span>
      `;
      field.appendChild(head);

      if (spec.type === "enum") {
        const select = document.createElement("select");
        for (const opt of spec.options) {
          const o = document.createElement("option");
          o.value = opt;
          o.textContent = opt;
          if (values[key] === opt) o.selected = true;
          select.appendChild(o);
        }
        select.addEventListener("change", () => onChange(key, select.value));
        field.appendChild(select);
      } else if (spec.type === "string") {
        const input = document.createElement("input");
        input.type = "text";
        input.value = values[key] ?? "";
        input.addEventListener("change", () => onChange(key, input.value));
        field.appendChild(input);
      } else {
        const range = document.createElement("input");
        range.type = "range";
        range.min = spec.min;
        range.max = spec.max;
        range.step = spec.step ?? (spec.type === "int" ? 1 : 0.01);
        range.value = values[key];
        range.addEventListener("input", () => {
          head.querySelector(".field__value").textContent = formatValue(
            key,
            range.value
          );
          onChange(key, range.value);
        });
        field.appendChild(range);
      }

      inner.appendChild(field);
    }

    panel.appendChild(inner);
    controlsEl.appendChild(panel);
  }
}

function onChange(key, raw) {
  const spec = specs[key];
  let val = raw;
  if (spec.type === "int") val = parseInt(raw, 10);
  else if (spec.type === "float") val = parseFloat(raw);
  values[key] = val;
  scheduleSave();
}

function scheduleSave() {
  clearTimeout(saveTimer);
  setStatus("pending…");
  saveTimer = setTimeout(saveAll, 180);
}

async function saveAll() {
  try {
    const res = await fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ values }),
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    values = data.values;
    setStatus("saved", "ok");
  } catch (err) {
    setStatus("save failed", "err");
    console.error(err);
  }
}

async function pollRuntime() {
  try {
    const res = await fetch("/api/runtime");
    const data = await res.json();
    if (data.error) {
      runtimeEl.textContent = "audio error";
      runtimeEl.className = "runtime runtime--err";
      return;
    }
    if (data.running) {
      const [r, g, b] = data.rgb;
      runtimeEl.textContent = data.beat
        ? `RGB ${r},${g},${b} BEAT`
        : `RGB ${r},${g},${b}`;
      runtimeEl.className = "runtime runtime--ok";
    } else {
      runtimeEl.textContent = "audio stopped";
      runtimeEl.className = "runtime runtime--err";
    }
  } catch {
    runtimeEl.textContent = "audio offline";
    runtimeEl.className = "runtime runtime--err";
  }
}

async function load() {
  const [schemaRes, settingsRes] = await Promise.all([
    fetch("/api/schema"),
    fetch("/api/settings"),
  ]);
  const schema = await schemaRes.json();
  const settings = await settingsRes.json();
  specs = schema.specs;
  values = settings.values;
  buildControls();
  setStatus("ready", "ok");
  pollRuntime();
  setInterval(pollRuntime, 400);
}

resetBtn.addEventListener("click", async () => {
  if (!confirm("Delete settings.local.json and revert to config.py defaults?")) return;
  const res = await fetch("/api/settings/reset", { method: "POST" });
  const data = await res.json();
  values = data.values;
  buildControls();
  setStatus("reset", "ok");
});

load();