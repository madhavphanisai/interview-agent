import React from "react";

export default function FeedbackModal({ open, onClose, score }) {
  if (!open) return null;

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 9999, display: "flex",
      alignItems: "center", justifyContent: "center"
    }}>
      <div onClick={onClose} style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.6)" }} />
      <div style={{
        position: "relative",
        minWidth: 320,
        maxWidth: "90%",
        borderRadius: 12,
        padding: 20,
        background: "linear-gradient(180deg,#0b1220,#111827)",
        color: "#e6eef6",
        boxShadow: "0 10px 30px rgba(2,6,23,0.6)"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 20 }}>Interview Feedback</h2>
            <div style={{ fontSize: 12, color: "#9aa6b2" }}>Quick summary</div>
          </div>
          <button onClick={onClose} style={{
            background: "transparent", border: "none", color: "#9aa6b2", cursor: "pointer", fontSize: 16
          }}>✕</button>
        </div>

        <div style={{ marginTop: 18, textAlign: "center" }}>
          <div style={{ fontSize: 48, fontWeight: 700 }}>{score !== null && score !== undefined ? `${score}/5` : '-'}</div>
          <div style={{ marginTop: 8, color: "#9aa6b2" }}>Overall score</div>
        </div>

        <div style={{ marginTop: 18, display:"flex", justifyContent:"flex-end" }}>
          <button onClick={onClose} style={{
            padding: "8px 14px", borderRadius: 8, border: "none",
            background: "linear-gradient(90deg,#2563eb,#7c3aed)", color: "white", cursor: "pointer"
          }}>Close</button>
        </div>
      </div>
    </div>
  );
}
