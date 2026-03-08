export interface RetrievalItem {
  product_id: number;
  score: number;
  payload: Record<string, unknown>;
}

export interface RetrievalResponse {
  request_id: string;
  latency_ms: number;
  results: RetrievalItem[];
  diagnostics: Record<string, unknown>;
}

export interface ProductDisplayItem {
  product_id: number;
  title: string;
  description: string;
  image_url: string;
}
