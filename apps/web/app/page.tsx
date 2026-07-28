"use client";

import { Settings } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Brand } from "@/components/Brand";
import { ProgressCard } from "@/components/ProgressCard";
import { UploadDropzone } from "@/components/UploadDropzone";
import { api, getAdminToken, setAdminToken } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [uploadPercent, setUploadPercent] = useState<number>();
  const [error, setError] = useState("");
  const [token, setToken] = useState("");

  useEffect(() => setToken(getAdminToken()), []);

  const upload = async (file: File) => {
    setError("");
    if (!token.trim()) {
      setError("Enter the administrator token before uploading a document.");
      return;
    }
    setAdminToken(token.trim());
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
      <nav>
        <Brand />
        <div className="nav-actions">
          <label className="token-field">
            Administrator token
            <input
              type="password"
              value={token}
              onChange={(event) => { setToken(event.target.value); setAdminToken(event.target.value.trim()); }}
            />
          </label>
          <Link className="nav-link" href="/settings"><Settings size={17} /> Settings</Link>
        </div>
      </nav>
      <section className="landing-content">
        {uploadPercent === undefined ? <UploadDropzone onFile={upload} /> : <ProgressCard uploadPercent={uploadPercent} />}
        {error && <div className="error-banner">{error}</div>}
      </section>
      <footer><span>Private by design</span><span>•</span><span>No analytics</span><span>•</span><span>Provider-agnostic</span></footer>
    </main>
  );
}
