import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { motion, AnimatePresence } from "framer-motion";
import "./App.css";

const pageTransition = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -10 },
  transition: { duration: 0.35, ease: "easeOut" },
};

const STEPS = [
  "Planning data cleanup",
  "Validating cleanup plan",
  "Cleaning dataset",
  "Profiling dataset",
  "Planning visualizations",
  "Generating visualizations",
  "Writing initial report",
  "Evaluating report quality",
  "Revising final report",
];

function App() {
  const [appState, setAppState] = useState("idle");
  const [file, setFile] = useState(null);
  const [report, setReport] = useState("");
  const [currentStep, setCurrentStep] = useState(-1);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [runId, setRunId] = useState(null);

  const handleUpload = async () => {
    if (!file) return;

    setAppState("executing");
    setReport("");
    setCurrentStep(-1);
    setCompletedSteps([]);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const runRes = await axios.post(
        "/run",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      const { run_id } = runRes.data;
      setRunId(run_id);

      await new Promise((resolve, reject) => {
        const es = new EventSource(`/progress/${run_id}`);

        es.onmessage = async (e) => {
          const event = JSON.parse(e.data);

          if (event.type === "task_started") {
            setCurrentStep(event.index);
          } else if (event.type === "task_completed") {
            setCompletedSteps((prev) => [...prev, event.index]);
          } else if (event.type === "done") {
            es.close();
            try {
              const reportRes = await axios.get(`/${event.report_path}`);
              setReport(reportRes.data);
              setAppState("completed");
            } catch (err) {
              reject(err);
            }
            resolve();
          } else if (event.type === "error") {
            es.close();
            reject(new Error(event.message));
          }
        };

        es.onerror = () => {
          es.close();
          reject(new Error("Connection lost"));
        };
      });
    } catch (err) {
      console.error(err);
      setAppState("error");
    }
  };

    const resetApp = () => {
    setFile(null);
    setReport("");
    setAppState("idle");
  };


  return (
    <div className="app-shell">
      <AnimatePresence mode="wait">
        {appState === "idle" && (
          <motion.div key="idle" {...pageTransition}>
            <EmptyState
              file={file}
              onFileSelect={setFile}
              onSubmit={handleUpload}
            />
          </motion.div>
        )}

        {appState === "executing" && (
          <motion.div key="executing" {...pageTransition}>
            <ExecutionState currentStep={currentStep} completedSteps={completedSteps} />
          </motion.div>
        )}

        {appState === "completed" && (
          <motion.div key="completed" {...pageTransition}>
            <ResultState report={report} runId={runId} onReset={resetApp} />
          </motion.div>
        )}

        {appState === "error" && (
          <motion.div key="error" {...pageTransition}>
            <ErrorState onReset={resetApp} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ---------------- STATES ---------------- */

function EmptyState({ file, onFileSelect, onSubmit }) {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) onFileSelect(dropped);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    if (!e.currentTarget.contains(e.relatedTarget)) setIsDragging(false);
  };

  const handleCardClick = () => {
    if (!file) inputRef.current.click();
  };

  return (
    <div className="centered">
      <h1 className="title">Agentic AI Powered Data Science</h1>
      <p className="subtitle">
        Upload a dataset to generate an AI-powered analysis
      </p>

      <div
        className={`upload-card ${isDragging ? "dragging" : ""}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleCardClick}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.json,.parquet,.xml,.avro"
          style={{ display: "none" }}
          onChange={(e) => onFileSelect(e.target.files[0])}
        />

        {!file ? (
          <>
            <div className="drop-icon">↑</div>
            <p className="drop-hint">Drag & drop your dataset here</p>
            <p className="drop-hint muted">or click to browse</p>
          </>
        ) : (
          <>
            <p className="filename">📄 {file.name}</p>
            <button
              className="primary-button"
              onClick={(e) => { e.stopPropagation(); onSubmit(); }}
            >
              Analyze Dataset
            </button>
            <button
              className="secondary-button"
              onClick={(e) => {
                e.stopPropagation();
                onFileSelect(null);
                inputRef.current.value = "";
              }}
            >
              Choose different file
            </button>
          </>
        )}

        <p className="file-hint">CSV · JSON · Parquet · XML · Avro</p>
      </div>
    </div>
  );
}

function ExecutionState({ currentStep, completedSteps }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (s) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}m ${sec.toString().padStart(2, "0")}s`;
  };

  return (
    <div className="centered">
      <h2>🧠 Analyzing Your Dataset</h2>
      <p className="muted elapsed">{formatTime(elapsed)}</p>

      <div className="step-list">
        {STEPS.map((label, i) => {
          const isDone = completedSteps.includes(i);
          const isActive = currentStep === i && !isDone;
          const isPending = !isDone && !isActive;

          return (
            <motion.div
              key={i}
              className={`step-row ${isDone ? "done" : isActive ? "active" : "pending"}`}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: isPending ? 0.35 : 1, x: 0 }}
              transition={{ delay: i * 0.05, duration: 0.25 }}
            >
              <span className="step-icon">
                {isDone ? "✓" : isActive ? <span className="step-spinner" /> : "○"}
              </span>
              <span className="step-label">{label}</span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

function ResultState({ report, runId, onReset }) {
  const downloadCleaned = async () => {
    const res = await fetch(`/download/${runId}/cleaned`);
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "cleaned_dataset.csv";
    a.click();
  };

  return (
    <motion.div
      className="result-wrapper"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      <div className="result-toolbar">
        <button className="primary-button" onClick={downloadCleaned}>
          Download Cleaned Dataset
        </button>
        <button className="primary-button" onClick={onReset}>
          New Analysis
        </button>
      </div>

      <div className="result-container markdown-container">
        <ReactMarkdown>{report}</ReactMarkdown>
      </div>
    </motion.div>
  );
}

function ErrorState({ onReset }) {
  return (
    <div className="centered">
      <h2>⚠️ Something went wrong</h2>
      <p className="muted">Please try again.</p>

      <button className="primary-button" onClick={onReset} style={{ marginTop: "15px"}}>
          ← Back to Home
        </button>
    </div>
  );
}

export default App;