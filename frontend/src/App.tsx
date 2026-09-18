import { useEffect, useRef, useState } from "react";
import { Header } from "./components/Header";
import { Hero } from "./components/Hero";
import { UploadCard } from "./components/UploadCard";
import { ProcessingPanel } from "./components/ProcessingPanel";
import { ErrorPanel } from "./components/ErrorPanel";
import { ResultsDashboard } from "./components/ResultsDashboard";
import { Footer } from "./components/Footer";
import { ApiRequestError, checkHealth, processDocument } from "./lib/api";
import type { HealthResponse, ProcessResponse, ProcessingStage } from "./types";

const DEFAULT_ALLOWED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png"];
const DEFAULT_MAX_FILE_SIZE_MB = 20;

function App() {
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [health, setHealth] = useState<HealthResponse | null>(null);

  const [stage, setStage] = useState<ProcessingStage>("idle");
  const [fileName, setFileName] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [result, setResult] = useState<ProcessResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const elapsedTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const processingStartedRef = useRef(false);

  useEffect(() => {
    checkHealth()
      .then((data) => {
        setHealth(data);
        setBackendStatus("online");
      })
      .catch(() => setBackendStatus("offline"));
  }, []);

  useEffect(() => {
    return () => {
      if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current);
    };
  }, []);

  const handleProcess = async (file: File) => {
    setFileName(file.name);
    setStage("uploading");
    setUploadProgress(0);
    setElapsedSeconds(0);
    setErrorMessage("");
    processingStartedRef.current = false;

    try {
      const data = await processDocument(file, (percent) => {
        setUploadProgress(percent);
        if (percent >= 100 && !processingStartedRef.current) {
          processingStartedRef.current = true;
          setStage("processing");
          elapsedTimerRef.current = setInterval(() => {
            setElapsedSeconds((prev) => prev + 1);
          }, 1000);
        }
      });

      if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current);
      setResult(data);
      setStage("success");
    } catch (error) {
      if (elapsedTimerRef.current) clearInterval(elapsedTimerRef.current);
      const message =
        error instanceof ApiRequestError
          ? error.message
          : "Something unexpected went wrong while processing this document.";
      setErrorMessage(message);
      setStage("error");
    }
  };

  const handleReset = () => {
    setStage("idle");
    setResult(null);
    setErrorMessage("");
    setUploadProgress(0);
    setElapsedSeconds(0);
  };

  const allowedExtensions = health?.allowed_extensions ?? DEFAULT_ALLOWED_EXTENSIONS;
  const maxFileSizeMb = health?.max_file_size_mb ?? DEFAULT_MAX_FILE_SIZE_MB;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <Header backendStatus={backendStatus} />
      <main className="mx-auto max-w-4xl px-4 pb-20 sm:px-6">
        {stage === "idle" && <Hero />}

        <section className="mx-auto max-w-2xl">
          {stage === "idle" && (
            <UploadCard
              allowedExtensions={allowedExtensions}
              maxFileSizeMb={maxFileSizeMb}
              onProcess={handleProcess}
              disabled={backendStatus === "offline"}
              disabledReason={
                backendStatus === "offline"
                  ? "Can't reach the processing server right now — please try again shortly."
                  : undefined
              }
            />
          )}

          {(stage === "uploading" || stage === "processing") && (
            <ProcessingPanel
              stage={stage}
              fileName={fileName}
              uploadProgress={uploadProgress}
              elapsedSeconds={elapsedSeconds}
            />
          )}

          {stage === "error" && <ErrorPanel message={errorMessage} onRetry={handleReset} />}
        </section>

        {stage === "success" && result && (
          <section className="mt-10">
            <ResultsDashboard result={result} onReset={handleReset} />
          </section>
        )}
      </main>
      <Footer />
    </div>
  );
}

export default App;
