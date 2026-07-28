"use client";

import { ArrowLeft, CheckCircle2, KeyRound, PlugZap, Save, ServerCog } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { Brand } from "@/components/Brand";
import { api } from "@/lib/api";
import type { Provider } from "@/lib/types";

const initial = {
  name: "Local translation",
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
  is_active: true,
};

export default function SettingsPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [form, setForm] = useState(initial);
  const [editing, setEditing] = useState<string>();
  const [token, setToken] = useState("");
  const [message, setMessage] = useState("");

  const load = () => api.providers().then(setProviders).catch((error) => setMessage(error.message));
  useEffect(() => {
    void load();
  }, []);

  const edit = (provider: Provider) => {
    setEditing(provider.id);
    setForm({
      ...initial,
      ...provider,
      api_key: "",
      custom_system_prompt: provider.custom_system_prompt ?? "",
      model: provider.model ?? "",
    });
  };

  const save = async (event: FormEvent) => {
    event.preventDefault();
    setMessage("Saving encrypted configuration…");
    try {
      await api.saveProvider(form, token, editing);
      setMessage("Provider configuration saved.");
      setEditing(undefined);
      setForm(initial);
      load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Configuration could not be saved");
    }
  };

  const test = async (id: string) => {
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
                <option value="openai_compatible">OpenAI compatible / Ollama</option>
                <option value="libretranslate">LibreTranslate</option>
              </select></label>
              <label className="wide">Base URL<input required type="url" value={form.base_url} placeholder="e.g. http://host.docker.internal:11434/v1" onChange={(e) => setForm({ ...form, base_url: e.target.value })} /></label>
              <label>Model name<input value={form.model} placeholder="e.g. qwen2.5:7b" onChange={(e) => setForm({ ...form, model: e.target.value })} /></label>
              <label>API key<input type="password" value={form.api_key} placeholder={editing ? "Leave blank to keep current key" : "Optional for local services"} onChange={(e) => setForm({ ...form, api_key: e.target.value })} /></label>
              <label>Timeout (seconds)<input type="number" min="5" max="600" value={form.timeout_seconds} onChange={(e) => setForm({ ...form, timeout_seconds: Number(e.target.value) })} /></label>
              <label>Maximum retries<input type="number" min="0" max="10" value={form.max_retries} onChange={(e) => setForm({ ...form, max_retries: Number(e.target.value) })} /></label>
              <label>Batch size<input type="number" min="1" max="100" value={form.batch_size} onChange={(e) => setForm({ ...form, batch_size: Number(e.target.value) })} /></label>
              <label>Context size<input type="number" min="256" value={form.context_size} onChange={(e) => setForm({ ...form, context_size: Number(e.target.value) })} /></label>
              <label>Temperature<input type="number" min="0" max="2" step="0.1" value={form.temperature} onChange={(e) => setForm({ ...form, temperature: Number(e.target.value) })} /></label>
              <label>Rate limit / minute<input type="number" min="1" value={form.rate_limit_per_minute} onChange={(e) => setForm({ ...form, rate_limit_per_minute: Number(e.target.value) })} /></label>
              <label className="wide">Custom system prompt<textarea value={form.custom_system_prompt} placeholder="Optional. The safe document-data boundary remains enforced." onChange={(e) => setForm({ ...form, custom_system_prompt: e.target.value })} /></label>
              <label className="wide">Administrator token<input type="password" required value={token} onChange={(e) => setToken(e.target.value)} /></label>
              <label className="check"><input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} /> Use as active provider</label>
            </div>
            <button className="primary" type="submit"><Save size={17} /> Save provider</button>
          </form>
          {message && <div className="settings-message"><CheckCircle2 size={17} /> {message}</div>}
        </section>
      </div>
    </main>
  );
}
