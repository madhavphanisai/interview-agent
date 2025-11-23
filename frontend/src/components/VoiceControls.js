// VoiceControls.js (forwardRef: exposes start()/stop())
import React, { useEffect, useRef, useState, forwardRef, useImperativeHandle } from "react";

const VoiceControls = forwardRef(function VoiceControls(
  { onResult, interimCallback, onStart, onStop, lang = "en-US" },
  ref
) {
  const recognitionRef = useRef(null);
  const [listening, setListening] = useState(false);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      recognitionRef.current = null;
      return;
    }
    const r = new SpeechRecognition();
    r.lang = lang;
    r.interimResults = true;
    r.maxAlternatives = 1;
    r.continuous = false; // single utterance
    recognitionRef.current = r;

    r.onresult = (event) => {
      let interim = "";
      let final = "";
      for (let i = 0; i < event.results.length; i++) {
        const res = event.results[i];
        if (res.isFinal) final += res[0].transcript;
        else interim += res[0].transcript;
      }
      if (interimCallback) interimCallback(interim);
      if (final && onResult) {
        onResult(final.trim());
      }
    };

    r.onend = () => {
      setListening(false);
      if (onStop) onStop();
    };

    r.onerror = (e) => {
      console.error("SpeechRecognition error:", e);
      setListening(false);
      if (onStop) onStop();
    };

    return () => {
      try {
        r.onresult = null;
        r.onend = null;
        r.onerror = null;
      } catch {}
    };
  }, [interimCallback, onResult, onStart, onStop, lang]);

  useImperativeHandle(ref, () => ({
    start: () => start(),
    stop: () => stop(),
    isListening: () => !!listening
  }));

  function start() {
    const r = recognitionRef.current;
    if (!r) return console.warn("SpeechRecognition unsupported.");
    try {
      r.start();
      setListening(true);
      if (onStart) onStart();
    } catch (err) {
      console.warn("Recognition start error:", err);
    }
  }

  function stop() {
    const r = recognitionRef.current;
    if (!r) return;
    try {
      r.stop();
    } catch (err) {
      console.warn("Recognition stop error:", err);
    }
    setListening(false);
    if (onStop) onStop();
  }

  return (
    <div style={{display:"flex", gap:8, alignItems:"center"}}>
      <button
        onClick={() => (listening ? stop() : start())}
        style={{
          padding: "8px 12px",
          background: listening ? "#e85" : "#08c",
          color: "white",
          border: "none",
          borderRadius: 6,
          cursor: "pointer"
        }}
      >
        {listening ? "Stop Recording" : "Start Recording"}
      </button>
      <small style={{color:"#666"}}>{listening ? "Listening..." : "Click to speak (Chrome/Edge recommended)"}</small>
    </div>
  );
});

export default VoiceControls;
