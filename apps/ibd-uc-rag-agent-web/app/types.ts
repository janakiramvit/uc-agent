export interface Citation {
  number: number;
  claimId: string;
  sourceTitle: string;
  sourceUrl: string;
  claimText: string;
  supportingExcerpt: string;
  exactLocator: string;
  evidenceLevel: string;
  confidence: string;
  limitations: string;
  applicabilityLimitations: string;
}

export interface ConflictEntry {
  topic: string;
  claimIds: string[];
  confidenceValues: string[];
  evidenceLevelValues: string[];
  reason: string;
}

export interface ConflictReport {
  has_conflicts: boolean;
  conflicts: ConflictEntry[];
}

export interface QueryPlan {
  segments: string[];
  identified_topics: string[];
  steps: string[];
}

export interface TraceEntry {
  node: string;
  output: unknown;
}

export type ChatStatus = "answered" | "unsupported" | "refused" | "llm_unavailable" | "error";

export interface ChatResponse {
  status: ChatStatus;
  answer: string;
  citations: Citation[];
  showSymptomCaveat: boolean;
  plan: QueryPlan | null;
  conflictReport: ConflictReport | null;
  vectorRetrievalStatus: string | null;
  llmProvider: string | null;
  llmModel: string | null;
  trace: TraceEntry[];
  visitedNodes: string[];
}

export interface ChatErrorResponse {
  error: string;
  message: string;
  retryAfterSeconds?: number;
  maxChars?: number;
  trace?: string;
}
