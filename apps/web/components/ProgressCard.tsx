"use client";

import { CircleStop, LoaderCircle } from "lucide-react";
import type { Job } from "@/lib/types";

const labels: Record<string, string> = {
  uploading: "Uploading",
  parsing_document: "Parsing document",
  detecting_text: "Detecting text",
  running_ocr: "Running OCR",
  detecting_source_language: "Detecting source language",
  translating: "Translating",
  rebuilding_layout: "Rebuilding layout",
  generating_preview: "Generating preview",
  preparing_export: "Preparing export",
  queued: "Waiting for a worker",
};

export function ProgressCard({ job, uploadPercent, onCancel }: {
  job?: Job;
  uploadPercent?: number;
  onCancel?: () => void;
}) {
  const percent = job?.progress_percent ?? uploadPercent ?? 0;
  const stage = job?.current_stage ?? "uploading";
  return (
    <div className="progress-card">
      <div className="progress-heading">
        <span className="progress-icon"><LoaderCircle className="spin" size={22} /></span>
        <div>
          <p className="eyebrow">PROCESSING DOCUMENT</p>
          <h2>{labels[stage] ?? stage.replaceAll("_", " ")}</h2>
          {job && job.total_pages > 0 && <p>Page {job.current_page} of {job.total_pages}</p>}
        </div>
        <strong>{Math.round(percent)}%</strong>
      </div>
      <div className="progress-track"><span style={{ width: `${percent}%` }} /></div>
      {onCancel && <button className="ghost danger" onClick={onCancel}><CircleStop size={16} /> Cancel</button>}
    </div>
  );
}

