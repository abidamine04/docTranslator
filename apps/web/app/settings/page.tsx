"use client";

import { ArrowLeft, CheckCircle2, KeyRound, PlugZap, Save, ServerCog } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Brand } from "@/components/Brand";
import { api, getAdminToken, setAdminToken } from "@/lib/api";
import type { ApplicationSettings, Provider } from "@/lib/types";

const initial = {
  name: "",
  provider_type: "openai_compatible",
  base_url: "",
  api_key: "",
  model: "",
  timeout_seconds: 120,
  max_retries: 2,
  batch_size: 12,
  context_size: 8192,
  temperature: 0.1,
  custom_system_prompt: "",
  rate_limit_per_minute: 60,
  max_output_tokens: 4096,
  chat_completions_path: "/chat/completions",
  models_path: "/models",
  translate_path: "/translate",
  custom_headers: "{}",
  verify_tls: true,
  is_active: false,
};

export default function SettingsPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [applicationSettings, setApplicationSettings] = useState<ApplicationSettings>();
  const [form, setForm] = useState(initial);
  const [editing, setEditing] = useState<string>();
  const [token, setToken] = useState("");
  const [message, setMessage] = useState("");

  const load = () => Promise.all([api.providers(), api.settings()])
    .then(([savedProviders, savedSettings]) => {
      setProviders(savedProviders);
      setApplicationSettings(savedSettings);
    }).catch((error) => setMessage(error.message));
  useEffect(() => {
    const stored = getAdminToken();
    setToken(stored);
    if (stored) void load();
  }, []);

  const edit = (provider: Provider) => {
    setEditing(provider.id);
    setForm({
      ...initial,
      ...provider,
      api_key: "",
      custom_system_prompt: provider.custom_system_prompt ?? "",
      model: provider.model ?? "",
      custom_headers: JSON.stringify(provider.custom_headers ?? {}, null, 2),
    });
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    setAdminToken(token.trim());
    setMessage("Saving encrypted configuration…");
    try {
      await api.saveProvider({
        ...form,
        custom_headers: JSON.parse(form.custom_headers || "{}"),
      }, token, editing);
      setMessage("Provider configuration saved.");
      setEditing(undefined);
      setForm(initial);
      load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Configuration could not be saved");
    }
  };

  const saveApplicationSettings = async (event: FormEvent) => {
    event.preventDefault();
    if (!applicationSettings) return;
    setMessage("Saving application settings...");
    try {
      const saved = await api.saveSettings(applicationSettings, token.trim());
      setApplicationSettings(saved);
      setMessage("Application settings saved and active immediately.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Settings could not be saved");
    }
  };

  const test = async (id: string) => {
    setAdminToken(token.trim());
    setMessage("Testing provider connection…");
    try {
      const result = await api.testProvider(id, token);
      setMessage(`Connection succeeded. Sample response: ${result.sample}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Connection failed");
    }
  };

  return (
    <main className="settings-shell">
      <nav><Brand /><Link className="nav-link" href="/"><ArrowLeft size={17} /> Back to documents</Link></nav>
      <div className="settings-layout">
        <aside>
          <p className="eyebrow">ADMINISTRATION</p>
          <h1>Settings</h1>
          <button className="active"><PlugZap size={18} /> Translation providers</button>
          <button disabled><ServerCog size={18} /> OCR engines <span>Soon</span></button>
          <div className="settings-note"><KeyRound size={17} /><p>API keys are encrypted server-side and never returned to this browser.</p></div>
        </aside>
        <section className="settings-content">
          <div className="settings-heading">
            <div><p className="eyebrow">TRANSLATION</p><h2>Provider configuration</h2><p>Connect a local service or an optional cloud endpoint. Nothing is hardcoded into the application.</p></div>
          </div>
          <div className="provider-cards">
            {providers.map((provider) => (
              <div className="provider-card" key={provider.id}>
                <div className="provider-icon"><ServerCog /></div>
                <div><h3>{provider.name} {provider.is_active && <span className="active-badge">Active</span>}</h3>
                  <p>{provider.provider_type.replace("_", " ")} · {provider.base_url}</p>
                  <small>{provider.model || "No model"} · key {provider.has_api_key ? "stored" : "not required"}</small>
                </div>
                <button className="ghost" onClick={() => edit(provider)}>Edit</button>
                <button className="ghost" onClick={() => test(provider.id)}>Test</button>
              </div>
            ))}
          </div>
          <form className="provider-form" onSubmit={save}>
            <div className="form-title"><h3>{editing ? "Edit provider" : "Add a provider"}</h3><p>All network and model behavior is adjustable here.</p></div>
            <div className="form-grid">
              <label>Name<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
              <label>Provider type<select value={form.provider_type} onChange={(e) => setForm({ ...form, provider_type: e.target.value })}>
                <option value="openai_compatible">OpenAI compatible</option>
                <option value="libretranslate">LibreTranslate</option>
              </select></label>
              <label className="wide">Base URL<input required type="url" value={form.base_url} placeholder="https://your-provider.example/v1" onChange={(e) => setForm({ ...form, base_url: e.target.value })} /></label>
              <label>Model name<input value={form.model} placeholder="your-model-name" onChange={(e) => setForm({ ...form, model: e.target.value })} /></label>
              <label>API key<input type="password" value={form.api_key} placeholder={editing ? "Leave blank to keep current key" : "Optional for local services"} onChange={(e) => setForm({ ...form, api_key: e.target.value })} /></label>
              <label>Timeout (seconds)<input type="number" min="5" max="600" value={form.timeout_seconds} onChange={(e) => setForm({ ...form, timeout_seconds: Number(e.target.value) })} /></label>
              <label>Maximum retries<input type="number" min="0" max="10" value={form.max_retries} onChange={(e) => setForm({ ...form, max_retries: Number(e.target.value) })} /></label>
              <label>Batch size<input type="number" min="1" max="100" value={form.batch_size} onChange={(e) => setForm({ ...form, batch_size: Number(e.target.value) })} /></label>
              <label>Context size<input type="number" min="256" value={form.context_size} onChange={(e) => setForm({ ...form, context_size: Number(e.target.value) })} /></label>
              <label>Temperature<input type="number" min="0" max="2" step="0.1" value={form.temperature} onChange={(e) => setForm({ ...form, temperature: Number(e.target.value) })} /></label>
              <label>Rate limit / minute<input type="number" min="1" value={form.rate_limit_per_minute} onChange={(e) => setForm({ ...form, rate_limit_per_minute: Number(e.target.value) })} /></label>
              <label>Maximum output tokens<input type="number" min="1" value={form.max_output_tokens} onChange={(e) => setForm({ ...form, max_output_tokens: Number(e.target.value) })} /></label>
              <label>Chat completions path<input value={form.chat_completions_path} onChange={(e) => setForm({ ...form, chat_completions_path: e.target.value })} /></label>
              <label>Models path<input value={form.models_path} onChange={(e) => setForm({ ...form, models_path: e.target.value })} /></label>
              <label>Translate path<input value={form.translate_path} onChange={(e) => setForm({ ...form, translate_path: e.target.value })} /></label>
              <label className="wide">Custom headers (JSON)<textarea value={form.custom_headers} onChange={(e) => setForm({ ...form, custom_headers: e.target.value })} /></label>
              <label className="wide">Custom system prompt<textarea value={form.custom_system_prompt} placeholder="Optional. The safe document-data boundary remains enforced." onChange={(e) => setForm({ ...form, custom_system_prompt: e.target.value })} /></label>
              <label className="wide">Administrator token<input type="password" required value={token} onChange={(e) => { setToken(e.target.value); setAdminToken(e.target.value.trim()); }} /></label>
              <label className="check"><input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Use as active provider</label>
              <label className="check"><input type="checkbox" checked={form.verify_tls} onChange={(e) => setForm({ ...form, verify_tls: e.target.checked })} /> Verify TLS certificates</label>
            </div>
            <button className="primary" type="submit"><Save size={17} /> Save provider</button>
          </form>
          {applicationSettings && <form className="provider-form" onSubmit={saveApplicationSettings}>
            <div className="form-title"><h3>Application settings</h3><p>General defaults, document limits, storage, and advanced processing controls.</p></div>
            <div className="form-grid">
              <label>Default target language<input value={applicationSettings.default_target_language} onChange={(e) => setApplicationSettings({ ...applicationSettings, default_target_language: e.target.value })} /></label>
              <label>Default translation tone<input value={applicationSettings.default_translation_tone} onChange={(e) => setApplicationSettings({ ...applicationSettings, default_translation_tone: e.target.value })} /></label>
              <label>OCR confidence threshold<input type="number" min="0" max="1" step="0.01" value={applicationSettings.ocr_confidence_threshold} onChange={(e) => setApplicationSettings({ ...applicationSettings, ocr_confidence_threshold: Number(e.target.value) })} /></label>
              <label>Maximum upload (MB)<input type="number" min="1" value={applicationSettings.max_upload_mb} onChange={(e) => setApplicationSettings({ ...applicationSettings, max_upload_mb: Number(e.target.value) })} /></label>
              <label>Maximum page count<input type="number" min="1" value={applicationSettings.max_page_count} onChange={(e) => setApplicationSettings({ ...applicationSettings, max_page_count: Number(e.target.value) })} /></label>
              <label>Retention period (days)<input type="number" min="0" value={applicationSettings.file_retention_days} onChange={(e) => setApplicationSettings({ ...applicationSettings, file_retention_days: Number(e.target.value) })} /></label>
              <label className="wide">Storage root<input value={applicationSettings.storage_root} onChange={(e) => setApplicationSettings({ ...applicationSettings, storage_root: e.target.value })} /></label>
              <label>Language detection sample (characters)<input type="number" min="100" value={applicationSettings.language_detection_sample_chars} onChange={(e) => setApplicationSettings({ ...applicationSettings, language_detection_sample_chars: Number(e.target.value) })} /></label>
              <label className="wide">Translation system prompt<textarea value={applicationSettings.translation_system_prompt} onChange={(e) => setApplicationSettings({ ...applicationSettings, translation_system_prompt: e.target.value })} /></label>
            </div>
            <button className="primary" type="submit"><Save size={17} /> Save application settings</button>
          </form>}
          {message && <div className="settings-message"><CheckCircle2 size={17} /> {message}</div>}
        </section>
      </div>
    </main>
  );
}
