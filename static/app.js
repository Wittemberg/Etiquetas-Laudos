const rows = document.querySelector("#rows");
const statusEl = document.querySelector("#status");
const uploadForm = document.querySelector("#uploadForm");
const pdfFile = document.querySelector("#pdfFile");
const selectAll = document.querySelector("#selectAll");
const sortSelect = document.querySelector("#sortSelect");
const editDialog = document.querySelector("#editDialog");
const editForm = document.querySelector("#editForm");
const fields = ["exam_number", "patient_name", "city", "district", "birth_date", "exam_date"];

let labels = [];

function setStatus(message) {
  statusEl.textContent = message;
}

async function loadLabels() {
  const response = await fetch(`/api/labels?sort=${encodeURIComponent(sortSelect.value)}`);
  labels = await response.json();
  renderRows();
}

function renderRows() {
  rows.innerHTML = "";
  for (const label of labels) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><input type="checkbox" class="rowCheck" value="${label.id}"></td>
      <td>${label.exam_number}</td>
      <td>${label.patient_name}</td>
      <td>${label.city}</td>
      <td>${label.district}</td>
      <td>${label.birth_date}</td>
      <td>${label.exam_date}</td>
      <td><button type="button" data-edit="${label.id}">Editar</button></td>
    `;
    rows.appendChild(tr);
  }
}

function selectedIds() {
  return [...document.querySelectorAll(".rowCheck:checked")].map((input) => Number(input.value));
}

async function download(endpoint, filename) {
  const ids = selectedIds();
  if (!ids.length) {
    setStatus("Selecione pelo menos uma etiqueta.");
    return;
  }
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  });
  if (!response.ok) {
    setStatus("Não foi possível gerar o arquivo.");
    return;
  }
  const blob = await response.blob();
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
  setStatus(`${filename} gerado.`);
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!pdfFile.files.length) {
    setStatus("Escolha um PDF para importar.");
    return;
  }
  const data = new FormData();
  data.append("file", pdfFile.files[0]);
  setStatus("Importando...");
  const response = await fetch("/api/import", { method: "POST", body: data });
  const result = await response.json();
  setStatus(`${result.inserted} importados, ${result.duplicated} duplicados ignorados.`);
  await loadLabels();
});

selectAll.addEventListener("change", () => {
  document.querySelectorAll(".rowCheck").forEach((input) => {
    input.checked = selectAll.checked;
  });
});

sortSelect.addEventListener("change", async () => {
  selectAll.checked = false;
  await loadLabels();
});

rows.addEventListener("click", (event) => {
  const button = event.target.closest("[data-edit]");
  if (!button) return;
  const label = labels.find((item) => item.id === Number(button.dataset.edit));
  document.querySelector("#editId").value = label.id;
  for (const field of fields) {
    document.querySelector(`#${field}`).value = label[field];
  }
  editDialog.showModal();
});

document.querySelector("#cancelEdit").addEventListener("click", () => editDialog.close());

editForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = document.querySelector("#editId").value;
  const payload = Object.fromEntries(fields.map((field) => [field, document.querySelector(`#${field}`).value]));
  const response = await fetch(`/api/labels/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    setStatus("Não foi possível salvar. Verifique duplicidade dos dados.");
    return;
  }
  editDialog.close();
  setStatus("Dados atualizados.");
  await loadLabels();
});

document.querySelector("#pdfBtn").addEventListener("click", () => download("/api/print/pdf", "etiquetas.pdf"));
document.querySelector("#docxBtn").addEventListener("click", () => download("/api/print/docx", "etiquetas.docx"));

loadLabels();
