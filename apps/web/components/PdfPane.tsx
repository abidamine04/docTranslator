"use client";

import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();

export function PdfPane({ file, page, scale, label, onPages }: {
  file: string;
  page: number;
  scale: number;
  label: string;
  onPages?: (count: number) => void;
}) {
  return (
    <section className="pdf-pane">
      <div className="pane-label">{label}</div>
      <div className="page-stage">
        <Document
          file={file}
          loading={<div className="pdf-loading">Loading page…</div>}
          error={<div className="pdf-error">This preview could not be rendered.</div>}
          onLoadSuccess={({ numPages }) => onPages?.(numPages)}
        >
          <Page pageNumber={page} scale={scale} renderAnnotationLayer renderTextLayer />
        </Document>
      </div>
    </section>
  );
}

