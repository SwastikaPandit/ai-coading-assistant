import { useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { downloadAllFiles, copyToClipboard } from "../utils/download";

const LANG_ICONS = {
  javascript:  "JS",
  typescript:  "TS",
  python:      "PY",
  json:        "{}",
  css:         "CSS",
  html:        "HTML",
  bash:        "SH",
  text:        "TXT",
};

export default function OutputPanel({ coderOutput, sessionId }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [copied,       setCopied]       = useState(false);

  const files = coderOutput?.files || [];

  // Auto-select first file when output arrives
  if (files.length && !selectedFile) {
    setSelectedFile(files[0].filename);
  }

  const activeFile = files.find(f => f.filename === selectedFile);

  function handleCopy() {
    if (!activeFile) return;
    copyToClipboard(activeFile.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="panel" style={{ display: "grid", gridTemplateColumns: "200px 1fr", borderRight: "none" }}>

      {/* File Tree */}
      <div style={{ borderRight: "1px solid #2d3148", display: "flex", flexDirection: "column" }}>
        <div className="panel-header">Files</div>

        {files.length === 0 ? (
          <div style={{ padding: "16px", fontSize: "12px", color: "#4a5068", lineHeight: 1.6 }}>
            Generated files will appear here...
          </div>
        ) : (
          <div className="file-tree">
            {files.map(file => (
              <div
                key={file.filename}
                className={`file-item ${selectedFile === file.filename ? "active" : ""}`}
                onClick={() => setSelectedFile(file.filename)}
              >
                <span style={{
                  fontSize: "9px",
                  fontWeight: 700,
                  background: "#2d3148",
                  padding: "1px 4px",
                  borderRadius: "3px",
                  color: "#7c83a0",
                  flexShrink: 0,
                }}>
                  {LANG_ICONS[file.language] || "?"}
                </span>
                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {file.filename.split("/").pop()}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Download All */}
        {files.length > 0 && (
          <div style={{ padding: "10px", borderTop: "1px solid #2d3148" }}>
            <button
              className="btn btn-secondary"
              style={{ width: "100%" }}
              onClick={() => downloadAllFiles(coderOutput)}
            >
              ⬇ Download All
            </button>
          </div>
        )}
      </div>

      {/* Code Viewer */}
      <div style={{ display: "flex", flexDirection: "column", overflow: "hidden" }}>

        {/* Viewer header */}
        <div className="panel-header" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <span>{activeFile?.filename || "Select a file"}</span>
          {activeFile && (
            <button className="btn btn-secondary" onClick={handleCopy}>
              {copied ? "✓ Copied" : "Copy"}
            </button>
          )}
        </div>

        {/* Code */}
        {activeFile ? (
          <div className="code-viewer">
            <SyntaxHighlighter
              language={activeFile.language || "text"}
              style={vscDarkPlus}
              customStyle={{
                margin: 0,
                background: "#0f1117",
                fontSize: "12px",
                minHeight: "100%",
                padding: "16px",
              }}
              showLineNumbers
            >
              {activeFile.content}
            </SyntaxHighlighter>
          </div>
        ) : (
          <div style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#4a5068",
            fontSize: "13px",
            flexDirection: "column",
            gap: "8px",
          }}>
            <span style={{ fontSize: "32px" }}>👩‍💻</span>
            <span>Your generated code will appear here</span>
          </div>
        )}
      </div>
    </div>
  );
}