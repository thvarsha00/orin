export type Language = "en" | "te" | "hi" | "ta" | "kn" | "ml" | "mr" | "bn";
export type Level = "beginner" | "intermediate" | "advanced";
export type ScriptPref = "auto" | "roman" | "native";

export interface Profile { display_name: string; preferred_language: Language; skill_level: Level; preferred_script: ScriptPref }
export interface User { id: number; email: string; profile: Profile }
export interface Conversation { id: number; title: string; language: Language; level: Level; created_at: string }
export interface ChatMessage {
  id?: number; role: "user" | "assistant"; content: string;
  has_image?: boolean;   // saved message with an image (fetched from the server by id)
  imageUrl?: string;     // local preview for a message sent in this session
  sources?: DocSource[]; // passages a document answer was built from
}

export type DocStatus = "queued" | "extracting" | "embedding" | "ready" | "failed";
export interface DocumentItem {
  id: number; filename: string; file_type: "pdf" | "txt" | "md"; file_size: number;
  page_count: number | null; chunk_count: number; status: DocStatus; error: string | null;
  created_at: string; updated_at: string | null;
}
export interface DocSource {
  document_id: number; document_name: string; page_number: number | null; snippet: string; score: number;
}
export interface DocumentsConfig {
  max_mb: number; types: string[]; embedding: { ready: boolean; model: string; hint: string | null };
}
export interface Health {
  status: string;
  ai: { provider: string; reachable: boolean; chat_model: string; chat_model_available: boolean;
        embed_model?: string; hint: string | null };
  vision?: { provider: string | null; model: string | null; configured: boolean; hint: string | null };
}
