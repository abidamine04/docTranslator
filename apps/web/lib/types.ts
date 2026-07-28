export type Job = {
  id: string;
  document_id: string;
  status: "queued" | "running" | "complete" | "complete_with_warnings" | "failed" | "cancelled";
  current_stage: string;
  current_page: number;
  total_pages: number;
  progress_percent: number;
  error_message?: string;
};

export type Quality = {
  text_detected: number;
  successfully_translated: number;
  failed: number;
  untranslated: number;
  low_confidence: number;
  overflow_warnings: number;
  translation_coverage: number;
  fully_translated: boolean;
};

export type DocumentRecord = {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  page_count: number;
  source_language?: string;
  target_language?: string;
  status: string;
  quality?: Quality;
};

export type ElementRecord = {
  id: string;
  page_number: number;
  bounding_box: { x: number; y: number; width: number; height: number };
  original_text: string;
  translated_text?: string;
  source_language?: string;
  target_language?: string;
  confidence: number;
  translation_status: string;
  style: Record<string, string | number>;
  reviewed: boolean;
};

export type Provider = {
  id: string;
  name: string;
  provider_type: "openai_compatible" | "libretranslate";
  base_url: string;
  has_api_key: boolean;
  model?: string;
  timeout_seconds: number;
  max_retries: number;
  batch_size: number;
  context_size: number;
  temperature: number;
  custom_system_prompt?: string;
  rate_limit_per_minute: number;
  is_active: boolean;
};

