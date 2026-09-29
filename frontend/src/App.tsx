import {
  ArrowDownToLine,
  Check,
  ChevronDown,
  CircleAlert,
  FileArchive,
  Image,
  LoaderCircle,
  LockKeyhole,
  RotateCcw,
  Sparkles,
  UploadCloud,
  X,
} from "lucide-react";
import {
  type ChangeEvent,
  type DragEvent,
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

const MAX_FILE_SIZE = 100 * 1024 * 1024;

type ProcessState = "idle" | "processing" | "success" | "error";

type Result = {
  accepted: number;
  rejected: number;
  downloadUrl: string;
};

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

async function getErrorMessage(response: Response) {
  try {
    const body = (await response.json()) as { detail?: string };
    return body.detail ?? "Não foi possível processar o arquivo.";
  } catch {
    return "Não foi possível processar o arquivo.";
  }
}

function App() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [threshold, setThreshold] = useState("");
  const [state, setState] = useState<ProcessState>("idle");
  const [error, setError] = useState("");
  const [result, setResult] = useState<Result | null>(null);

  useEffect(() => {
    return () => {
      if (result?.downloadUrl) URL.revokeObjectURL(result.downloadUrl);
    };
  }, [result]);

  function resetResult() {
    if (result?.downloadUrl) URL.revokeObjectURL(result.downloadUrl);
    setResult(null);
    setError("");
    setState("idle");
  }

  function selectFile(nextFile: File | undefined) {
    if (!nextFile) return;
    resetResult();

    if (!nextFile.name.toLowerCase().endsWith(".zip")) {
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      setError("Escolha um arquivo no formato ZIP.");
      setState("error");
      return;
    }
    if (nextFile.size > MAX_FILE_SIZE) {
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
      setError("O arquivo ultrapassa o limite de 100 MB.");
      setState("error");
      return;
    }

    setFile(nextFile);
  }

  function handleInput(event: ChangeEvent<HTMLInputElement>) {
    selectFile(event.target.files?.[0]);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    selectFile(event.dataTransfer.files[0]);
  }

  function removeFile() {
    setFile(null);
    resetResult();
    if (inputRef.current) inputRef.current.value = "";
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;

    resetResult();
    setState("processing");
    const data = new FormData();
    data.append("archive", file);
    if (threshold) data.append("threshold", threshold);

    try {
      const response = await fetch("/api/process", { method: "POST", body: data });
      if (!response.ok) throw new Error(await getErrorMessage(response));

      const blob = await response.blob();
      setResult({
        accepted: Number(response.headers.get("X-Photos-Accepted") ?? 0),
        rejected: Number(response.headers.get("X-Photos-Rejected") ?? 0),
        downloadUrl: URL.createObjectURL(blob),
      });
      setState("success");
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Não foi possível processar o arquivo.",
      );
      setState("error");
    }
  }

  return (
    <div className="app-shell">
      <main className="main-layout">
        <section className="hero" aria-labelledby="page-title">
          <div className="eyebrow"><span /> Triagem inteligente de imagens</div>
          <h1 id="page-title">Fotos nítidas.<br /><em>Vistoria em ordem.</em></h1>
          <p className="hero-copy">
            Remova automaticamente fotos tremidas sem perder a sequência do
            percurso. Um pacote organizado, pronto para o seu relatório.
          </p>

          <div className="benefits">
            <div><span><Check size={16} /></span><p><strong>Ordem preservada</strong>As fotos mantêm a sequência original.</p></div>
            <div><span><Image size={16} /></span><p><strong>Análise automática</strong>Nitidez avaliada imagem por imagem.</p></div>
            <div><span><ArrowDownToLine size={16} /></span><p><strong>Resultado pronto</strong>ZIP renomeado com relatório incluso.</p></div>
          </div>
        </section>

        <section className="workspace" aria-labelledby="upload-title">
          <div className="workspace-heading">
            <div>
              <span className="step-label">PASSO 1 DE 1</span>
              <h2 id="upload-title">Envie suas fotos</h2>
            </div>
            <span className="file-limit">ZIP · até 100 MB</span>
          </div>

          <form onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              className="sr-only"
              type="file"
              accept=".zip,application/zip"
              onChange={handleInput}
              tabIndex={-1}
            />

            {!file ? (
              <div
                className={`drop-zone ${isDragging ? "is-dragging" : ""}`}
                onClick={() => inputRef.current?.click()}
                onDragEnter={(event) => { event.preventDefault(); setIsDragging(true); }}
                onDragOver={(event) => event.preventDefault()}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
                }}
                role="button"
                tabIndex={0}
              >
                <span className="upload-illustration"><UploadCloud size={30} /></span>
                <strong>Arraste o arquivo ZIP aqui</strong>
                <p>ou selecione direto do seu dispositivo</p>
                <button className="choose-button" type="button">Escolher arquivo</button>
              </div>
            ) : (
              <div className="selected-file">
                <span className="file-icon"><FileArchive size={25} /></span>
                <div className="file-details">
                  <strong>{file.name}</strong>
                  <span>{formatFileSize(file.size)} · Pronto para processar</span>
                </div>
                <span className="ready-check"><Check size={16} /></span>
                <button type="button" className="remove-button" onClick={removeFile} aria-label="Remover arquivo">
                  <X size={19} />
                </button>
              </div>
            )}

            <button
              type="button"
              className="settings-toggle"
              onClick={() => setShowSettings((visible) => !visible)}
              aria-expanded={showSettings}
            >
              <span>Ajustar sensibilidade <small>Opcional</small></span>
              <ChevronDown className={showSettings ? "is-open" : ""} size={18} />
            </button>

            {showSettings && (
              <div className="settings-panel">
                <label htmlFor="threshold">
                  Limiar de nitidez
                  <span>Quanto maior, mais rigorosa será a filtragem.</span>
                </label>
                <input
                  id="threshold"
                  type="number"
                  min="0"
                  step="0.1"
                  placeholder="Padrão: 100"
                  value={threshold}
                  onChange={(event) => setThreshold(event.target.value)}
                />
              </div>
            )}

            {state === "error" && (
              <div className="message error-message" role="alert">
                <CircleAlert size={20} /><div><strong>Não foi possível continuar</strong><p>{error}</p></div>
              </div>
            )}

            {state === "success" && result && (
              <div className="result-card" role="status">
                <div className="result-title"><span><Check size={19} /></span><div><strong>Processamento concluído</strong><p>Seu pacote está pronto para baixar.</p></div></div>
                <div className="result-numbers">
                  <div><strong>{result.accepted}</strong><span>aprovadas</span></div>
                  <div><strong>{result.rejected}</strong><span>removidas</span></div>
                </div>
                <a className="download-button" href={result.downloadUrl} download="fotos_filtradas.zip">
                  <ArrowDownToLine size={18} /> Baixar resultado
                </a>
              </div>
            )}

            {state !== "success" && (
              <button className="process-button" type="submit" disabled={!file || state === "processing"}>
                {state === "processing" ? <><LoaderCircle className="spinning" size={19} /> Analisando fotos…</> : <><Sparkles size={18} /> Processar fotos</>}
              </button>
            )}

            {state === "success" && (
              <button className="new-process-button" type="button" onClick={removeFile}>
                <RotateCcw size={17} /> Processar outro arquivo
              </button>
            )}
          </form>

          <p className="privacy-footer"><LockKeyhole size={13} /> Seus arquivos são usados somente durante o processamento.</p>
        </section>
      </main>
    </div>
  );
}

export default App;
