"use client";

import { Settings } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Brand } from "@/components/Brand";
import { ProgressCard } from "@/components/ProgressCard";
import { UploadDropzone } from "@/components/UploadDropzone";
import { api } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [uploadPercent, setUploadPercent] = useState<number>();
  const [error, setError] = useState("");

  const upload = async (file: File) => {
    setError("");
    setUploadPercent(0);
    try {
      const result = await api.upload(file, setUploadPercent);
      sessionStorage.setItem(`job:${result.document.id}`, result.job.id);
      router.push(`/documents/${result.document.id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Upload failed");
      setUploadPercent(undefined);
    }
  };

  return (
    <main className="landing-shell">
      <nav><Brand /><Link className="nav-link" href="/settings"><Settings size={17} /> Settings</Link></nav>
      <section className="landing-content">
        {uploadPercent === undefined ? <UploadDropzone onFile={upload} /> : <ProgressCard uploadPercent={uploadPercent} />}
        {error && <div className="error-banner">{error}</div>}
      </section>
      <footer><span>Private by design</span><span>•</span><span>No analytics</span><span>•</span><span>Provider-agnostic</span></footer>
    </main>
  );
}
