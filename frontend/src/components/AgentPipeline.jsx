const AGENTS = [
    {
      key: "planner",
      name: "Planner Agent",
      desc: "Breaks down your prompt into a structured project plan with files, features, and tech stack.",
      icon: "🗂️",
    },
    {
      key: "architect",
      name: "Architect Agent",
      desc: "Defines system architecture, inter-component contracts, and directory structure.",
      icon: "🏗️",
    },
    {
      key: "coder",
      name: "Coder Agent",
      desc: "Generates complete, runnable code for every file in the project.",
      icon: "👩‍💻",
    },
  ];
  
  function AgentCard({ agent, status, output }) {
    return (
      <div className={`agent-card ${status}`}>
        <div className="agent-name">
          <span className={`status-dot ${status}`} />
          <span>{agent.icon}</span>
          <span>{agent.name}</span>
          <span style={{ marginLeft: "auto", fontSize: "10px", color: statusColor(status) }}>
            {statusLabel(status)}
          </span>
        </div>
        <div className="agent-desc">{agent.desc}</div>
  
        {/* Show summary when completed */}
        {status === "completed" && output && (
          <div style={{
            marginTop: "10px",
            padding: "8px",
            background: "#0f1117",
            borderRadius: "6px",
            fontSize: "11px",
            color: "#7c83a0",
            lineHeight: 1.6,
          }}>
            {agent.key === "planner" && (
              <>
                <div><strong style={{ color: "#a78bfa" }}>Project:</strong> {output.project_name}</div>
                <div><strong style={{ color: "#a78bfa" }}>Stack:</strong> {output.tech_stack?.join(", ")}</div>
                <div><strong style={{ color: "#a78bfa" }}>Files:</strong> {output.files?.length} planned</div>
              </>
            )}
            {agent.key === "architect" && (
              <>
                <div><strong style={{ color: "#a78bfa" }}>Files:</strong> {output.files?.length} defined</div>
                <div style={{ marginTop: 4, fontFamily: "monospace", fontSize: "10px", whiteSpace: "pre", overflowX: "auto", color: "#4a5068" }}>
                  {output.directory_tree?.slice(0, 200)}
                </div>
              </>
            )}
            {agent.key === "coder" && (
              <>
                <div><strong style={{ color: "#a78bfa" }}>Generated:</strong> {output.files?.length} files</div>
                <div><strong style={{ color: "#a78bfa" }}>Languages:</strong> {[...new Set(output.files?.map(f => f.language))].join(", ")}</div>
              </>
            )}
          </div>
        )}
  
        {status === "failed" && (
          <div style={{ marginTop: 8, fontSize: "11px", color: "#ef4444" }}>
            ✗ Agent failed — check your API key or try again
          </div>
        )}
      </div>
    );
  }
  
  function statusLabel(status) {
    switch (status) {
      case "running":   return "● Running";
      case "completed": return "✓ Done";
      case "failed":    return "✗ Failed";
      default:          return "Waiting";
    }
  }
  
  function statusColor(status) {
    switch (status) {
      case "running":   return "#a78bfa";
      case "completed": return "#10b981";
      case "failed":    return "#ef4444";
      default:          return "#4a5068";
    }
  }
  
  export default function AgentPipeline({
    agentStatuses,
    plannerOutput,
    architectOutput,
    coderOutput,
    generationTime,
    error,
  }) {
    const outputs = {
      planner:   plannerOutput,
      architect: architectOutput,
      coder:     coderOutput,
    };
  
    return (
      <div className="panel" style={{ padding: "16px", overflowY: "auto" }}>
        <div className="panel-header" style={{ margin: "-16px -16px 16px" }}>
          Agent Pipeline
        </div>
  
        {AGENTS.map((agent, i) => (
          <div key={agent.key}>
            <AgentCard
              agent={agent}
              status={agentStatuses[agent.key]}
              output={outputs[agent.key]}
            />
            {/* Arrow between agents */}
            {i < AGENTS.length - 1 && (
              <div style={{ textAlign: "center", color: "#3a3f55", fontSize: "16px", margin: "2px 0" }}>
                ↓
              </div>
            )}
          </div>
        ))}
  
        {/* Generation time */}
        {generationTime && (
          <div className="timer" style={{ textAlign: "center", marginTop: "12px" }}>
            ⚡ Generated in {generationTime}s
          </div>
        )}
  
        {/* Error */}
        {error && (
          <div style={{
            marginTop: "12px",
            padding: "10px",
            background: "#1f0f0f",
            border: "1px solid #ef4444",
            borderRadius: "6px",
            fontSize: "12px",
            color: "#ef4444",
          }}>
            ✗ {error}
          </div>
        )}
      </div>
    );
  }