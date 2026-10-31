const form = document.querySelector("#assessment-form");
const errorBox = document.querySelector("#error");
const result = document.querySelector("#result");
const emptyState = document.querySelector("#empty-state");
const submitButton = form.querySelector("button[type='submit']");

document.querySelector("#load-example").addEventListener("click", () => {
  form.requester.value = "Kadir Demir";
  form.department.value = "Research & Development";
  form.vendor.value = "Fabrikam Analytics Ltd";
  form.amount_eur.value = "128000";
  form.description.value = "Cloud-based quality inspection service processing production images and employee identifiers.";
  form.data_classification.value = "restricted";
  form.contains_personal_data.checked = true;
  form.single_source.checked = true;
  form.urgent.checked = true;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.textContent = "";
  submitButton.disabled = true;
  submitButton.querySelector("span").textContent = "Agents are assessing…";

  const data = new FormData(form);
  const payload = {
    requester: data.get("requester"),
    department: data.get("department"),
    vendor: data.get("vendor"),
    amount_eur: Number(data.get("amount_eur")),
    description: data.get("description"),
    data_classification: data.get("data_classification"),
    contains_personal_data: data.has("contains_personal_data"),
    single_source: data.has("single_source"),
    urgent: data.has("urgent"),
  };

  try {
    const response = await fetch("/api/v1/assessments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const body = await response.json();
      throw new Error(body.detail?.[0]?.msg || body.detail || "Assessment failed");
    }
    renderResult(await response.json());
  } catch (error) {
    errorBox.textContent = error.message;
  } finally {
    submitButton.disabled = false;
    submitButton.querySelector("span").textContent = "Run agent workflow";
  }
});

function renderResult(data) {
  emptyState.hidden = true;
  result.hidden = false;

  const badge = document.querySelector("#risk-badge");
  badge.textContent = `${data.risk_level} risk`;
  badge.className = `badge ${data.risk_level}`;
  document.querySelector("#status").textContent = data.status.replaceAll("_", " ");
  document.querySelector("#recommendation").textContent = data.recommendation;
  document.querySelector("#summary").textContent = data.executive_summary;
  document.querySelector("#route").innerHTML = data.approval_route
    .map((item) => `<span>${escapeHtml(item)}</span>`).join("");
  document.querySelector("#reasons").innerHTML = data.reasons
    .map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  document.querySelector("#trace").innerHTML = data.agent_trace.map((step) => `
    <article>
      <header><strong>${escapeHtml(step.agent)}</strong><span>${step.duration_ms.toFixed(1)} ms</span></header>
      <p>${escapeHtml(step.summary)}</p>
    </article>`).join("");
  document.querySelector("#evidence").innerHTML = data.policy_evidence.map((item) => `
    <article>
      <strong>${escapeHtml(item.section)} · relevance ${item.relevance.toFixed(2)}</strong>
      <p>${escapeHtml(item.excerpt)}</p>
    </article>`).join("");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[character]);
}

