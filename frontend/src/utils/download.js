import JSZip from "jszip";
import { saveAs } from "file-saver";

export async function downloadAllFiles(coderOutput) {
  if (!coderOutput?.files?.length) return;

  const zip = new JSZip();
  const projectFolder = zip.folder(coderOutput.project_name || "generated-project");

  coderOutput.files.forEach((file) => {
    projectFolder.file(file.filename, file.content);
  });

  const blob = await zip.generateAsync({ type: "blob" });
  saveAs(blob, `${coderOutput.project_name || "project"}.zip`);
}

export function copyToClipboard(text) {
  navigator.clipboard.writeText(text).catch(() => {
    // Fallback for older browsers
    const el = document.createElement("textarea");
    el.value = text;
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
  });
}

export function exportSession(sessionId, data) {
  const payload = {
    session_id:        sessionId,
    exported_at:       new Date().toISOString(),
    original_prompt:   data.originalPrompt,
    planner_output:    data.plannerOutput,
    architect_output:  data.architectOutput,
    coder_output:      data.coderOutput,
    chat_history:      data.chatHistory,
  };

  const blob = new Blob(
    [JSON.stringify(payload, null, 2)],
    { type: "application/json" }
  );
  saveAs(blob, `session-${sessionId?.slice(0, 8) || "export"}.json`);
}