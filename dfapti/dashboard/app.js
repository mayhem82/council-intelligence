async function loadJSON(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.json();
}

function badge(text, cssClass) {
  return `<span class="badge ${cssClass}">${text}</span>`;
}

function classificationCounts(entries) {
  const counts = { ACCEPTED: 0, HELD: 0, REJECTED: 0, PENDING: 0 };
  for (const e of entries) {
    if (counts[e.classification] !== undefined) counts[e.classification]++;
  }
  return counts;
}

function latestUpdate(entries) {
  const dates = entries.map(e => e.recorded_at).filter(Boolean).sort();
  return dates.length ? dates[dates.length - 1] : "No evidence yet";
}

async function renderDashboard() {
  const root = document.getElementById("case-list");
  try {
    const { cases } = await loadJSON("cases/index.json");
    const register = await loadJSON("evidence/register.json");

    if (!cases.length) {
      root.innerHTML = '<p class="empty-state">No active cases.</p>';
      return;
    }

    const cards = await Promise.all(cases.map(async (caseId) => {
      const c = await loadJSON(`cases/${caseId}/case.json`);
      const entries = register.entries.filter(e => e.case_id === caseId);
      const counts = classificationCounts(entries);
      const updated = latestUpdate(entries);
      return `
        <div class="case-card">
          <h2>${c.case_id} — ${c.title}</h2>
          <div class="case-meta">
            <span>${badge(c.status, c.status.toLowerCase())}</span>
            <span><strong>Last update:</strong> ${updated}</span>
            <span><strong>Evidence:</strong> Accepted: ${counts.ACCEPTED} · Held: ${counts.HELD} · Rejected: ${counts.REJECTED} · Pending: ${counts.PENDING}</span>
          </div>
          <p class="muted">${c.investigation_objective}</p>
          <a class="open-case" href="cases/${caseId}/index.html">Open Case →</a>
        </div>`;
    }));

    root.innerHTML = cards.join("\n");
  } catch (err) {
    root.innerHTML = `<p class="empty-state">Unable to load case register: ${err.message}</p>`;
  }
}

document.addEventListener("DOMContentLoaded", renderDashboard);
