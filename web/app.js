const state = { run: null };

const $ = (selector) => document.querySelector(selector);
const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

const runButton = $("#run-intake");
const emptyState = $("#empty-state");
const results = $("#results");
const toast = $("#toast");

function notify(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2600);
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

function artifactMap(run) {
  return Object.fromEntries(run.artifacts.map((artifact) => [artifact.id, artifact]));
}

function openAssertions(run) {
  const reviewed = new Set(run.reviews.map((decision) => decision.assertion_id));
  return run.assertions.filter((assertion) =>
    ["conflicted", "review_required"].includes(assertion.status) && !reviewed.has(assertion.id)
  );
}

function openFactKeys(run) {
  return new Set(openAssertions(run).map((assertion) =>
    `${assertion.subject_id}::${assertion.predicate}`
  ));
}

function renderMetrics(run) {
  const open = openFactKeys(run).size;
  const cards = [
    ["Source artifacts", run.artifacts.length, ""],
    ["Assertions", run.assertions.length, ""],
    ["Conflicts", run.conflicts.filter((item) => item.status === "open").length, "warn"],
    ["Open reviews", open, open ? "warn" : "good"],
    ["Effective facts", run.facts.length, "good"],
  ];
  $("#metrics").innerHTML = cards.map(([label, value, tone]) => `
    <div class="metric ${tone}"><span>${label}</span><strong>${value}</strong></div>
  `).join("");
}

function renderReviews(run) {
  const artifacts = artifactMap(run);
  const groups = new Map();
  for (const assertion of openAssertions(run)) {
    const items = groups.get(`${assertion.subject_id}::${assertion.predicate}`) || [];
    items.push(assertion);
    groups.set(`${assertion.subject_id}::${assertion.predicate}`, items);
  }
  const reviewCount = groups.size;
  $("#review-count").textContent = `${reviewCount} open`;
  if (!groups.size) {
    $("#review-list").innerHTML = `
      <div class="no-reviews"><b>Review queue cleared</b>Every promoted fact has passed its gate.</div>
    `;
    return;
  }
  $("#review-list").innerHTML = [...groups.entries()].map(([factKey, candidates]) => {
    const label = candidates.length > 1 ? "conflicting claims" : "confirmation required";
    const rows = candidates
      .sort((a, b) => b.authority - a.authority || b.confidence - a.confidence)
      .map((candidate) => {
        const evidence = candidate.evidence[0];
        const artifact = artifacts[evidence.artifact_id];
        return `
          <div class="candidate">
            <div>
              <div class="candidate-value">${escapeHtml(JSON.stringify(candidate.value))}</div>
              <div class="candidate-meta">${escapeHtml(artifact.filename)} · authority ${candidate.authority} · confidence ${(candidate.confidence * 100).toFixed(0)}%</div>
              <blockquote>“${escapeHtml(evidence.quote)}”</blockquote>
            </div>
            <button class="approve-button" data-review-id="${candidate.id}" type="button">Use this evidence</button>
          </div>
        `;
      }).join("");
    return `
      <article class="review-group">
        <div class="review-title"><code>${escapeHtml(factKey)}</code><span>${label}</span></div>
        ${rows}
      </article>
    `;
  }).join("");
}

function renderFacts(run) {
  const assertions = Object.fromEntries(run.assertions.map((item) => [item.id, item]));
  const artifacts = artifactMap(run);
  const facts = [...run.facts].sort((a, b) =>
    `${a.subject_id}.${a.predicate}`.localeCompare(`${b.subject_id}.${b.predicate}`)
  );
  $("#facts-list").innerHTML = facts.map((fact) => {
    const assertion = assertions[fact.assertion_ids[0]];
    const evidence = assertion.evidence[0];
    const artifact = artifacts[evidence.artifact_id];
    return `
      <div class="fact-row">
        <div class="fact-key"><span>${escapeHtml(fact.subject_id)} · ${escapeHtml(fact.predicate)}</span><span>v${fact.version}</span></div>
        <div class="fact-value"><i></i>${escapeHtml(JSON.stringify(fact.value))}</div>
        <div class="fact-evidence">${escapeHtml(artifact.filename)} · page ${evidence.page}</div>
      </div>
    `;
  }).join("");
}

function renderAudit(run) {
  $("#audit-track").innerHTML = run.audit_events.map((event) => `
    <div class="audit-event">
      <small>EVENT ${String(event.sequence).padStart(2, "0")}</small>
      <b>${escapeHtml(event.event_type.replaceAll("_", " "))}</b>
      <code>${escapeHtml(event.event_hash.slice(0, 16))}…</code>
    </div>
  `).join("");
}

async function renderRun(run) {
  state.run = run;
  emptyState.classList.add("hidden");
  results.classList.remove("hidden");
  $("#workspace-actions").classList.remove("hidden");
  $("#run-title").textContent = "Evidence, decisions, and promoted truth.";
  $("#run-id").textContent = `run ${run.id.slice(0, 8)}`;
  $("#provider-note").textContent = `Extraction provider: ${run.extraction_provider}`;
  renderMetrics(run);
  renderReviews(run);
  renderFacts(run);
  renderAudit(run);
  const exported = await request(`/api/runs/${run.id}/export`);
  $("#audit-status").textContent = exported.audit.verified ? "✓ chain verified" : "chain invalid";
}

async function createRun() {
  runButton.disabled = true;
  runButton.querySelector("span").textContent = "Extracting evidence…";
  try {
    const run = await request("/api/demo/runs", { method: "POST" });
    await renderRun(run);
    $("#workspace").scrollIntoView({ behavior: "smooth", block: "start" });
    notify("Trusted intake completed: 12 assertions assessed");
  } catch (error) {
    notify(error.message);
  } finally {
    runButton.disabled = false;
    runButton.querySelector("span").textContent = "Run trusted intake";
  }
}

async function reviewAssertion(assertionId, button) {
  if (!state.run) return;
  button.disabled = true;
  button.textContent = "Recording…";
  try {
    const run = await request(`/api/runs/${state.run.id}/reviews`, {
      method: "POST",
      body: JSON.stringify({
        chosen_assertion_id: assertionId,
        reviewer: "demo-reviewer",
        rationale: "Selected after comparing source authority and direct evidence.",
      }),
    });
    await renderRun(run);
    notify("Decision appended and eligible fact promoted");
  } catch (error) {
    button.disabled = false;
    button.textContent = "Use this evidence";
    notify(error.message);
  }
}

async function loadLatestRun() {
  try {
    const runs = await request("/api/runs");
    if (runs.length) {
      const run = await request(`/api/runs/${runs[0].id}`);
      await renderRun(run);
    }
  } catch (error) {
    notify(error.message);
  }
}

runButton.addEventListener("click", createRun);
$("#view-method").addEventListener("click", () =>
  $("#method").scrollIntoView({ behavior: "smooth" })
);
$("#export-run").addEventListener("click", () => {
  if (state.run) window.open(`/api/runs/${state.run.id}/export`, "_blank", "noopener");
});
$("#review-list").addEventListener("click", (event) => {
  const button = event.target.closest("[data-review-id]");
  if (button) reviewAssertion(button.dataset.reviewId, button);
});

loadLatestRun();
