const form = document.querySelector("#upload-form");
const archiveInput = document.querySelector("#archive");
const thresholdInput = document.querySelector("#threshold");
const dropZone = document.querySelector("#drop-zone");
const fileLabel = document.querySelector("#file-label");
const submitButton = document.querySelector("#submit-button");
const statusBox = document.querySelector("#status");
const statusTitle = document.querySelector("#status-title");
const statusMessage = document.querySelector("#status-message");

function setSelectedFile(file) {
  const transfer = new DataTransfer();
  transfer.items.add(file);
  archiveInput.files = transfer.files;
  fileLabel.textContent = file.name;
}

archiveInput.addEventListener("change", () => {
  if (archiveInput.files.length) {
    fileLabel.textContent = archiveInput.files[0].name;
  }
});

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("is-dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("is-dragging");
  });
});

dropZone.addEventListener("drop", (event) => {
  const [file] = event.dataTransfer.files;
  if (file) setSelectedFile(file);
});

function showStatus(kind, title, message) {
  statusBox.hidden = false;
  statusBox.className = `status ${kind ? `is-${kind}` : ""}`;
  statusTitle.textContent = title;
  statusMessage.textContent = message;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function errorMessage(response) {
  try {
    const body = await response.json();
    return body.detail || "Não foi possível processar o arquivo.";
  } catch {
    return "Não foi possível processar o arquivo.";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const [file] = archiveInput.files;
  if (!file) return;

  const data = new FormData();
  data.append("archive", file);
  if (thresholdInput.value) data.append("threshold", thresholdInput.value);

  submitButton.disabled = true;
  showStatus("", "Analisando suas fotos…", "Isso pode levar alguns instantes.");

  try {
    const response = await fetch("/api/process", { method: "POST", body: data });
    if (!response.ok) throw new Error(await errorMessage(response));

    const accepted = response.headers.get("X-Photos-Accepted") || "0";
    const rejected = response.headers.get("X-Photos-Rejected") || "0";
    downloadBlob(await response.blob(), "fotos_filtradas.zip");
    showStatus(
      "done",
      "Processamento concluído",
      `${accepted} fotos aprovadas e ${rejected} removidas. O download começou.`,
    );
  } catch (error) {
    showStatus("error", "Algo deu errado", error.message);
  } finally {
    submitButton.disabled = false;
  }
});
