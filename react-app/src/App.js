import React, { useState } from "react";
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

function App() {
  const [appState, setAppState] = useState("idle");
  const [file, setFile] = useState(null);
  const [report, setReport] = useState("");

  const handleUpload = async () => {
    if (!file) return;

    setAppState("executing");
    setReport("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const runRes = await axios.post(
        "/run",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      const reportRes = await axios.get(
        `/${runRes.data.report_path}`
      );

      setReport(reportRes.data);
      setAppState("completed");
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
            <ExecutionState />
          </motion.div>
        )}

        {appState === "completed" && (
          <motion.div key="completed" {...pageTransition}>
            <ResultState report={report} onReset={resetApp} />
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
  return (
    <div className="centered">
      <h1 className="title">Agentic AI Powered Data Science</h1>
      <p className="subtitle">
        Upload a dataset to generate an AI-powered analysis
      </p>

      <div className="upload-card">
        {/* Always show the file input */}
        <input
          type="file"
          accept=".csv,.json,.parquet,.xml,.avro"
          onChange={(e) => onFileSelect(e.target.files[0])}
        />

        {/* Only show Analyze button and filename AFTER a file is selected */}
        {file && (
          <>
            <button className="primary-button" onClick={onSubmit}>
              Analyze Dataset
            </button>
            <p className="filename">📄 {file.name}</p>
          </>
        )}
      </div>
    </div>
  );
}

function ExecutionState() {
  const agents = [
    "🧹 Data Engineer Agent Cleaning Data",
    "📊 Analyst Agent Performing Exploratory Data Analysis",
    "✍️ Writer Agent Drafting Report",
  ];

  return (
    <div className="centered">
      <h2>🧠 Analyzing Your Dataset</h2>

      <div className="spinner" />
      <p className="muted">This may take a minute…</p>

      <motion.div
        className="agent-list"
        initial="hidden"
        animate="visible"
        variants={{
          visible: { transition: { staggerChildren: 0.2 } },
        }}
      >
        {agents.map((text, i) => (
          <motion.p
            key={i}
            variants={{
              hidden: { opacity: 0, y: 5 },
              visible: { opacity: 1, y: 0 },
            }}
          >
            {text}
          </motion.p>
        ))}
      </motion.div>
    </div>
  );
}

function ResultState({ report, onReset }) {
const downloadCleaned = async () => {
    const res = await fetch("http://localhost:10000/download/cleaned");
    const blob = await res.blob();

    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "cleaned_dataset.csv";
    a.click();
  };

  return (
    <motion.div
      className="result-container markdown-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >

      <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px" }}>
        <button className="primary-button" onClick={downloadCleaned}>
          Download Cleaned Dataset
        </button>

        <button className="primary-button" onClick={onReset}>
          New Analysis
        </button>
      </div>
      
      <ReactMarkdown>{report}</ReactMarkdown>
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