import { useState } from "react";
import InputPanel    from "./components/InputPanel";
import AgentPipeline from "./components/AgentPipeline";
import OutputPanel   from "./components/OutputPanel";
import ChatPanel     from "./components/ChatPanel";
import { useWebSocket } from "./hooks/useWebSocket";
import { exportSession  } from "./utils/download";
export default function App() {
  const {
    generate,
    agentStatuses,
    plannerOutput,
    architectOutput,
    coderOutput,
    isGenerating,
    generationTime,
    sessionId,
    error,
  } = useWebSocket();

  const [liveCoderOutput, setLiveCoderOutput] = useState(null);

  // Use chat-refined output if available, otherwise use pipeline output
  const displayOutput = liveCoderOutput || coderOutput;

  function handleExport() {
    exportSession(sessionId, {
      originalPrompt:  null,
      plannerOutput,
      architectOutput,
      coderOutput:     displayOutput,
      chatHistory:     [],
    });
  }

  return (
    <div className="app">

      {/* Top bar */}
      <div className="topbar">
        <h1>⚡ AI Coding Assistant</h1>
        <span style={{ fontSize: "11px", color: "#4a5068" }}>
          Planner → Architect → Coder
        </span>
      </div>

      {/* Left: Input */}
      <InputPanel
        onGenerate={generate}
        isGenerating={isGenerating}
        agentStatuses={agentStatuses}
      />

      {/* Middle: Agent Pipeline */}
      <AgentPipeline
        agentStatuses={agentStatuses}
        plannerOutput={plannerOutput}
        architectOutput={architectOutput}
        coderOutput={displayOutput}
        generationTime={generationTime}
        error={error}
      />

      {/* Right: split into Output + Chat */}
      <div style={{
        display:             "grid",
        gridTemplateRows:    "1fr 280px",
        borderLeft:          "1px solid #2d3148",
        overflow:            "hidden",
      }}>
        <OutputPanel
          coderOutput={displayOutput}
          sessionId={sessionId}
        />
        <div style={{ borderTop: "1px solid #2d3148" }}>
          <ChatPanel
            sessionId={sessionId}
            coderOutput={displayOutput}
            onCodeUpdate={setLiveCoderOutput}
            exportSession={handleExport}
          />
        </div>
      </div>

    </div>
  );
}