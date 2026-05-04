import { useState, useRef, useCallback } from "react";

const WS_URL = "ws://localhost:8000/ws/generate";

export function useWebSocket() {
  const [agentStatuses, setAgentStatuses] = useState({
    planner:   "pending",
    architect: "pending",
    coder:     "pending",
  });
  const [plannerOutput,   setPlannerOutput]   = useState(null);
  const [architectOutput, setArchitectOutput] = useState(null);
  const [coderOutput,     setCoderOutput]     = useState(null);
  const [isGenerating,    setIsGenerating]    = useState(false);
  const [generationTime,  setGenerationTime]  = useState(null);
  const [sessionId,       setSessionId]       = useState(null);
  const [error,           setError]           = useState(null);

  const wsRef     = useRef(null);
  const startTime = useRef(null);

  const reset = useCallback(() => {
    setAgentStatuses({ planner: "pending", architect: "pending", coder: "pending" });
    setPlannerOutput(null);
    setArchitectOutput(null);
    setCoderOutput(null);
    setGenerationTime(null);
    setError(null);
  }, []);

  const generate = useCallback((prompt, settings = {}) => {
    reset();
    setIsGenerating(true);
    startTime.current = Date.now();

    // Close any existing connection
    if (wsRef.current) wsRef.current.close();

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ prompt, settings }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      switch (msg.type) {
        case "session":
          setSessionId(msg.session_id);
          break;

        case "agent_status":
          setAgentStatuses(prev => ({
            ...prev,
            [msg.agent]: msg.status,
          }));
          break;

        case "agent_complete":
          setAgentStatuses(prev => ({
            ...prev,
            [msg.agent]: "completed",
          }));
          if (msg.agent === "planner")   setPlannerOutput(msg.output);
          if (msg.agent === "architect") setArchitectOutput(msg.output);
          if (msg.agent === "coder")     setCoderOutput(msg.output);
          break;

        case "done":
          setIsGenerating(false);
          setGenerationTime(
            ((Date.now() - startTime.current) / 1000).toFixed(1)
          );
          break;

        case "error":
          setError(msg.message || "Something went wrong");
          setIsGenerating(false);
          break;

        default:
          break;
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection failed. Is the backend running?");
      setIsGenerating(false);
    };

    ws.onclose = () => {
      setIsGenerating(false);
    };
  }, [reset]);

  return {
    generate,
    reset,
    agentStatuses,
    plannerOutput,
    architectOutput,
    coderOutput,
    isGenerating,
    generationTime,
    sessionId,
    error,
  };
}