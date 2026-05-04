import { useState } from "react";

export default function InputPanel({ onGenerate, isGenerating, agentStatuses }) {
  const [prompt, setPrompt] = useState("");
  const [apiKey, setApiKey] = useState(
    () => localStorage.getItem("openai_api_key") || ""
  );

  const activeAgent = Object.entries(agentStatuses).find(
    ([, status]) => status === "running"
  )?.[0];

  const statusMessage = activeAgent
    ? `${activeAgent.charAt(0).toUpperCase() + activeAgent.slice(1)} is thinking...`
    : isGenerating
    ? "Starting pipeline..."
    : null;

  function handleGenerate() {
    if (!prompt.trim() || !apiKey.trim() || isGenerating) return;
    localStorage.setItem("openai_api_key", apiKey);
    onGenerate(prompt.trim(), { api_key: apiKey, model: "gpt-4o", temperature: 0.3 });
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleGenerate();
  }

  return (
    <div className="panel input-panel" style={{ padding: "16px", gap: "12px", display: "flex", flexDirection: "column" }}>
      <div className="panel-header" style={{ margin: "-16px -16px 0", padding: "12px 16px" }}>
        Input
      </div>

      {/* API Key */}
      <div style={{ marginTop: "12px" }}>
        <label style={{ fontSize: "11px", color: "#7c83a0", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.8px", display: "block", marginBottom: "6px" }}>
          OpenAI API Key
        </label>
        <input
          type="password"
          value={apiKey}
          onChange={e => setApiKey(e.target.value)}
          placeholder="sk-..."
          style={{
            width: "100%",
            background: "#1a1d27",
            border: "1px solid #2d3148",
            borderRadius: "6px",
            color: "#e2e8f0",
            padding: "8px 12px",
            fontSize: "13px",
            outline: "none",
            fontFamily: "inherit",
          }}
        />
      </div>

      {/* Prompt */}
      <div>
        <label style={{ fontSize: "11px", color: "#7c83a0", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.8px", display: "block", marginBottom: "6px" }}>
          Describe your app
        </label>
        <textarea
          rows={10}
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={`e.g. "Build me a React todo app with local storage"\n\nTip: Cmd+Enter to generate`}
          disabled={isGenerating}
        />
      </div>

      {/* Status */}
      {statusMessage && (
        <div style={{
          fontSize: "12px",
          color: "#a78bfa",
          background: "#1a1020",
          border: "1px solid #3d1f6e",
          borderRadius: "6px",
          padding: "8px 12px",
          display: "flex",
          alignItems: "center",
          gap: "8px",
        }}>
          <span style={{ animation: "pulse 1s infinite", display: "inline-block", width: 8, height: 8, borderRadius: "50%", background: "#7c3aed" }} />
          {statusMessage}
        </div>
      )}

      {/* Generate button */}
      <button
        className="btn btn-primary"
        onClick={handleGenerate}
        disabled={isGenerating || !prompt.trim() || !apiKey.trim()}
      >
        {isGenerating ? "Generating..." : "Generate  ⌘↵"}
      </button>

      {/* Re-generate hint */}
      {!isGenerating && (
        <p style={{ fontSize: "11px", color: "#4a5068", textAlign: "center" }}>
          Modify prompt and click Generate to re-run
        </p>
      )}
    </div>
  );
}