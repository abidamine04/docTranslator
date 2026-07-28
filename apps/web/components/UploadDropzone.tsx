"use client";

import { motion } from "framer-motion";
import { FileText, LockKeyhole, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";

export function UploadDropzone({ onFile }: { onFile: (file: File) => void }) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const accept = (files: FileList | null) => {
    const file = files?.[0];
    if (file) onFile(file);
  };

  return (
    <motion.div
      className={`dropzone ${dragging ? "dragging" : ""}`}
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55 }}
      onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => { event.preventDefault(); setDragging(false); accept(event.dataTransfer.files); }}
    >
      <div className="document-orbit" aria-hidden>
        <motion.div
          className="paper"
          animate={{ y: [0, -8, 0], rotate: [-1.5, 1.5, -1.5] }}
          transition={{ repeat: Infinity, duration: 5, ease: "easeInOut" }}
        >
          <FileText size={45} strokeWidth={1.3} />
          <span /><span /><span className="short" />
        </motion.div>
        <div className="orbit-ring" />
      </div>
      <p className="eyebrow">YOUR DOCUMENT, EVERY LANGUAGE</p>
      <h1>Translate the words.<br />Keep the design.</h1>
      <p className="lede">Upload a document and preserve its pages, positioning, and visual rhythm while every text block stays reviewable.</p>
      <button className="upload-button" onClick={() => input.current?.click()}>
        <UploadCloud size={19} /> Choose a PDF
      </button>
      <p className="drop-copy">or drop your document anywhere in this panel</p>
      <input ref={input} hidden type="file" accept=".pdf,application/pdf" onChange={(e) => accept(e.target.files)} />
      <div className="supported"><span>PDF</span><span>Native text</span><span>Scanned pages flagged</span></div>
      <div className="privacy"><LockKeyhole size={14} /> Files stay on your configured server</div>
    </motion.div>
  );
}

