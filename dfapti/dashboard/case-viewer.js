function getCaseIdFromPath() {
  const parts = window.location.pathname.split("/").filter(Boolean);
  const idx = parts.lastIndexOf("cases");
  if (idx !== -1 && parts.length > idx + 1) return parts[idx + 1];
  return null;
}

function badge(text, cssClass) {
  return `<span class="badge ${cssClass}">${text}</span>`;
}

async function loadJSON(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.json();
}

function documentCell(e) {
  if (!e.source_url) {
    return `${e.document_title} <span class='muted'>(source link not yet confirmed)</span>`;
  }
  return `<a href="${e.source_url}" target="_blank" rel="noopener noreferrer">${e.document_title}</a>`;
}

let allEntries = [];

function renderEvidence(filter) {
  const tbody = document.getElementById("evidence-body");
  const rows = allEntries.filter(e => filter === "ALL" || e.classification === filter);
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No evidence in this filter.</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(e => `
    <tr>
      <td>${e.evidence_id}</td>
      <td>${e.publication_date || "<span class='muted'>unconfirmed</span>"}</td>
      <td>${e.source_authority}</td>
      <td>${documentCell(e)}</td>
      <td>${badge(e.classification, e.classification.toLowerCase())}</td>
      <td>${e.confidence}</td>
      <td class="muted">PF(H,E)=${e.proof_of_fact.score} — ${e.verification_notes}</td>
    </tr>`).join("\n");
}

async function main() {
  const caseId = getCaseIdFromPath();
  if (!caseId) {
    document.getElementById("overview").innerHTML = `<p class="empty-state">Could not determine case ID from URL.</p>`;
    return;
  }

  const [caseData, timeline, register] = await Promise.all([
    loadJSON("case.json"),
    loadJSON("timeline.json"),
    loadJSON("../../evidence/register.json")
  ]);

  document.title = `${caseData.case_id} — ${caseData.title}`;
  document.getElementById("case-title").textContent = `${caseData.case_id} — ${caseData.title}`;
  document.getElementById("case-tagline").innerHTML = `${caseData.category} · ${caseData.jurisdiction} · ${badge(caseData.status, caseData.status.toLowerCase())}`;

  document.getElementById("overview").innerHTML = `
    <div class="case-meta">
      <span><strong>Case ID:</strong> ${caseData.case_id}</span>
      <span><strong>Created:</strong> ${caseData.created_date}</span>
      <span><strong>Responsible module:</strong> ${caseData.responsible_module}</span>
    </div>
    <p><strong>Objective:</strong> ${caseData.investigation_objective}</p>
    <p><strong>Scope:</strong> ${caseData.scope}</p>
    <p><strong>Primary sources:</strong> ${caseData.primary_sources.join(", ")}</p>
  `;

  document.querySelector("#timeline-table tbody").innerHTML = timeline.events.map(ev => `
    <tr>
      <td>${ev.date}</td>
      <td>${ev.event}</td>
      <td>${ev.evidence_ids.join(", ")}</td>
      <td>${ev.status_change}</td>
    </tr>`).join("\n");

  allEntries = register.entries.filter(e => e.case_id === caseId);
  renderEvidence("ALL");

  document.querySelectorAll("#filters button").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("#filters button").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      renderEvidence(btn.dataset.filter);
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  main().catch(err => {
    document.getElementById("overview").innerHTML = `<p class="empty-state">Failed to load case: ${err.message}</p>`;
  });
});
