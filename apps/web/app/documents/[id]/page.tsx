"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Check, ChevronLeft, ChevronRight, Download, Edit3, FileWarning, LayoutPanelLeft,
  Maximize, Minus, PanelLeftClose, RotateCw, Search, Settings, ZoomIn,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Brand } from "@/components/Brand";
import { ProgressCard } from "@/components/ProgressCard";
import { API_URL, api } from "@/lib/api";
import type { DocumentRecord, ElementRecord, Job, Provider } from "@/lib/types";

const PdfPane = dynamic(() => import("@/components/PdfPane").then((module) => module.PdfPane), { ssr: false });

export default function Workspace() {
  const { id } = useParams<{ id: string }>();
  const [document, setDocument] = useState<DocumentRecord>();
  const [elements, setElements] = useState<ElementRecord[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [job, setJob] = useState<Job>();
  const [activeJobId, setActiveJobId] = useState<string>();
  const [target, setTarget] = useState("");
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [scale, setScale] = useState(0.95);
  const [view, setView] = useState<"split" | "original" | "translated">("split");
  const [selected, setSelected] = useState<ElementRecord>();
  const [draft, setDraft] = useState("");
  const [exportId, setExportId] = useState<string>();
  const [message, setMessage] = useState("");

  const refresh = useCallback(async () => {
    const [doc, blocks, configured, savedSettings] = await Promise.all([
      api.document(id), api.elements(id), api.providers(), api.settings(),
    ]);
    setDocument(doc);
    setElements(blocks);
    setProviders(configured);
    setTarget((current) => current || savedSettings.default_target_language);
  }, [id]);

  useEffect(() => { refresh().catch((error) => setMessage(error.message)); }, [refresh]);

  useEffect(() => {
    setActiveJobId(sessionStorage.getItem(`job:${id}`) ?? undefined);
  }, [id]);

  useEffect(() => {
    if (!activeJobId) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const poll = async () => {
      try {
        const next = await api.job(activeJobId);
        if (stopped) return;
        setJob(next);
        if (["complete", "complete_with_warnings", "failed", "cancelled"].includes(next.status)) {
          sessionStorage.removeItem(`job:${id}`);
          setActiveJobId(undefined);
          await refresh();
          return;
        }
        timer = setTimeout(poll, 750);
      } catch (error) {
        if (!stopped) setMessage(error instanceof Error ? error.message : "Job status could not be loaded");
      }
    };
    void poll();
    return () => {
      stopped = true;
      if (timer) clearTimeout(timer);
    };
  }, [activeJobId, id, refresh]);
  const startTranslation = async () => {
    setMessage("");
    try {
      const active = providers.find((provider) => provider.is_active);
      const next = await api.translate(id, target, active?.id);
      setJob(next);
      sessionStorage.setItem(`job:${id}`, next.id);
      setActiveJobId(next.id);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Translation could not start");
    }
  };

  const createExport = async () => {
    setMessage("Preparing searchable PDF…");
    try {
      const result = await api.export(id);
      setExportId(result.id);
      setMessage("Export ready.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Export failed");
    }
  };

  const downloadExport = async () => {
    if (!exportId) return;
    setMessage("Downloading export…");
    try {
      const blob = await api.downloadExport(exportId);
      const url = URL.createObjectURL(blob);
      const link = window.document.createElement("a");
      link.href = url;
      link.download = "translated.pdf";
      link.click();
      URL.revokeObjectURL(url);
      setMessage("Download started.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Download failed");
    }
  };
  const selectBlock = (block: ElementRecord) => {
    setSelected(block);
    setDraft(block.translated_text ?? "");
    setPage(block.page_number);
  };

  const saveBlock = async () => {
    if (!selected) return;
    await api.updateElement(selected.id, draft);
    await refresh();
    setSelected({ ...selected, translated_text: draft, translation_status: "manually_edited" });
  };

  const issues = useMemo(
    () => elements.filter((element) => ["failed", "low_confidence", "unsupported"].includes(element.translation_status)),
    [elements],
  );
  const originalUrl = `${API_URL}/api/documents/${id}/file`;
  const translatedUrl = exportId ? `${API_URL}/api/exports/${exportId}/download` : originalUrl;
  const running = job && ["queued", "running"].includes(job.status);

  if (!document) return <main className="workspace loading-workspace">Opening workspace…</main>;

  return (
    <main className="workspace">
      <header className="workspace-top">
        <Link href="/"><Brand /></Link>
        <div className="file-meta">
          <strong>{document.filename}</strong>
          <span>{document.page_count || "—"} pages · {(document.size_bytes / 1048576).toFixed(1)} MB</span>
        </div>
        <div className="language-flow">
          <span className="source-pill">{(document.source_language ?? "Detecting").toUpperCase()}</span>
          <span>→</span>
          <select value={target} onChange={(event) => setTarget(event.target.value)} aria-label="Target language">
            <option value="en">English</option><option value="fr">French</option>
            <option value="ar">Arabic</option><option value="de">German</option>
            <option value="es">Spanish</option><option value="zh">Chinese</option>
            <option value="ja">Japanese</option><option value="he">Hebrew</option>
          </select>
          <button className="primary compact" onClick={startTranslation} disabled={Boolean(running)}>
            {running ? "Translating…" : "Translate"}
          </button>
        </div>
        <button className="icon-button" title="Search"><Search size={18} /></button>
        <Link href="/settings" className="icon-button" title="Settings"><Settings size={18} /></Link>
        <button className="download-button" onClick={exportId ? downloadExport : createExport}>
          <Download size={17} />
          {exportId ? "Download" : "Export"}
        </button>
      </header>

      {running && <div className="job-drawer"><ProgressCard job={job} onCancel={() => api.cancel(id)} /></div>}
      {message && <div className="workspace-message">{message}</div>}

      <div className="reader-grid">
        <aside className="left-rail">
          <button className="rail-active"><LayoutPanelLeft size={19} /><span>Pages</span></button>
          <button><FileWarning size={19} /><span>Review</span>{issues.length > 0 && <em>{issues.length}</em>}</button>
          <button><Edit3 size={19} /><span>Blocks</span></button>
          <div className="rail-pages">
            {Array.from({ length: document.page_count }, (_, index) => (
              <button key={index} className={page === index + 1 ? "active" : ""} onClick={() => setPage(index + 1)}>
                <span>{index + 1}</span>
              </button>
            ))}
          </div>
        </aside>

        <section className="reader">
          <div className="reader-toolbar">
            <div className="segmented">
              <button className={view === "original" ? "active" : ""} onClick={() => setView("original")}>Original</button>
              <button className={view === "split" ? "active" : ""} onClick={() => setView("split")}>Side by side</button>
              <button className={view === "translated" ? "active" : ""} onClick={() => setView("translated")}>Translation</button>
            </div>
            <div className="page-controls">
              <button onClick={() => setPage(Math.max(1, page - 1))}><ChevronLeft size={17} /></button>
              <span><input value={page} onChange={(e) => setPage(Math.min(pages, Math.max(1, Number(e.target.value))))} /> / {pages}</span>
              <button onClick={() => setPage(Math.min(pages, page + 1))}><ChevronRight size={17} /></button>
            </div>
            <div className="zoom-controls">
              <button onClick={() => setScale(Math.max(0.5, scale - 0.1))}><Minus size={17} /></button>
              <span>{Math.round(scale * 100)}%</span>
              <button onClick={() => setScale(Math.min(2, scale + 0.1))}><ZoomIn size={17} /></button>
              <button title="Rotate"><RotateCw size={17} /></button>
              <button title="Fullscreen" onClick={() => window.document.documentElement?.requestFullscreen()}><Maximize size={17} /></button>
            </div>
          </div>
          <div className={`viewer-panes ${view}`}>
            {view !== "translated" && <PdfPane file={originalUrl} page={page} scale={scale} label="ORIGINAL" onPages={setPages} />}
            {view !== "original" && (
              <PdfPane file={translatedUrl} page={page} scale={scale} label={exportId ? "TRANSLATION" : "TRANSLATION PREVIEW PENDING"} />
            )}
          </div>
        </section>

        <aside className="review-panel">
          <div className="panel-title"><div><p className="eyebrow">REVIEW MODE</p><h3>Text blocks</h3></div><PanelLeftClose size={18} /></div>
          <div className="quality-strip">
            <div><strong>{document.quality?.translation_coverage ?? 0}%</strong><span>coverage</span></div>
            <div><strong>{document.quality?.failed ?? 0}</strong><span>failed</span></div>
            <div><strong>{document.quality?.overflow_warnings ?? 0}</strong><span>overflow</span></div>
          </div>
          {selected ? (
            <div className="block-editor">
              <button className="back-link" onClick={() => setSelected(undefined)}>← All blocks</button>
              <label>Original text<textarea value={selected.original_text} readOnly /></label>
              <label>Translated text<textarea value={draft} onChange={(event) => setDraft(event.target.value)} /></label>
              <div className="block-facts">
                <span>Page <strong>{selected.page_number}</strong></span>
                <span>Confidence <strong>{Math.round(selected.confidence * 100)}%</strong></span>
                <span>Status <strong>{selected.translation_status}</strong></span>
                <span>Font <strong>{String(selected.style.font_family ?? "Unknown")}</strong></span>
              </div>
              <button className="primary full" onClick={saveBlock}>Save edit</button>
              <button className="ghost full" onClick={() => api.reviewElement(selected.id).then(refresh)}><Check size={16} /> Mark reviewed</button>
            </div>
          ) : (
            <div className="block-list">
              {elements.length === 0 && <p className="empty-list">Text blocks appear after analysis.</p>}
              {elements.map((block) => (
                <button key={block.id} onClick={() => selectBlock(block)}>
                  <span className={`status-dot ${block.translation_status}`} />
                  <div><strong>{block.translated_text || block.original_text}</strong><small>Page {block.page_number} · {block.translation_status}</small></div>
                  <ChevronRight size={15} />
                </button>
              ))}
            </div>
          )}
        </aside>
      </div>
    </main>
  );
}
