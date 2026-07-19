export interface StaticAssetBinding {
  fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response>;
}

export interface NarrativeRateLimitBinding {
  limit(options: { key: string }): Promise<{ success: boolean }>;
}

export interface WorkerEnv {
  ASSETS: StaticAssetBinding;
  EVIDENCEOPS_MODE: "fixture" | "openai";
  NARRATIVE_GLOBAL_RATE_LIMITER: NarrativeRateLimitBinding;
  NARRATIVE_RATE_LIMITER: NarrativeRateLimitBinding;
  OPENAI_API_KEY?: string;
  OPENAI_MODEL: "gpt-5.6-terra";
}
