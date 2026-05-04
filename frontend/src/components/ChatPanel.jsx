import { useState } from "react";
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "https://ai-coading-assistant.onrender.com";

export default function ChatPanel({ sessionId, coderOutput, onCodeUpdate, exportSession }) {
  const [messages,  setMessages]  = useState([]);
  const [input,     setInput]     = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSend() {
    if (!input.trim() || !sessionId || isLoading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", text: userMessage }]);
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        session_id: sessionId,
        message:    userMessage,
      });

      if (response.data.coder_output) {
        onCodeUpdate(response.data.coder_output);
        setMessages(prev => [...prev, {
          role: "assistant",
          text: "✓ Code updated! Check the output panel for changes.",
        }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: "assistant",
        text: "✗ Failed to update code. Please try again.",
      }]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="panel" style={{ borderRight: "none", gridColumn: "span 1" }}>
      <div className="panel-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span>Refinement Chat</span>
        {sessionId && (
          <button className="btn btn-secondary" onClick={exportSession}>
            ⬇ Export Session
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div style={{
            flex: 1,
            display:        "flex",
            flexDirection:  "column",
            alignItems:     "center",
            justifyContent: "center",
            color:          "#4a5068",
            fontSize:       "12px",
            textAlign:      "center",
            gap:            "8px",
            padding:        "20px",
            marginTop:      "40px",
          }}>
            <span style={{ fontSize: "28px" }}>💬</span>
            <span>After generating, ask follow-up questions here.</span>
            <span style={{ color: "#3a3f55" }}>
              e.g. "Add dark mode" or "Add authentication"
            </span>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble ${msg.role}`}>
            {msg.text}
          </div>
        ))}

        {isLoading && (
          <div className="chat-bubble assistant" style={{ color: "#7c83a0" }}>
            <span style={{ animation: "pulse 1s infinite", display: "inline-block" }}>
              Updating code...
            </span>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="chat-input-row">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={sessionId ? "Refine your app..." : "Generate first to enable chat"}
          disabled={!sessionId || isLoading}
        />
        <button
          className="btn btn-primary"
          style={{ width: "auto", padding: "8px 16px" }}
          onClick={handleSend}
          disabled={!sessionId || isLoading || !input.trim()}
        >
          Send
        </button>
      </div>
    </div>
  );
}