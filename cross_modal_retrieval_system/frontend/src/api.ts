import type { RetrievalResponse } from "./types";

const API_BASE = "/api/v1";

async function parseResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function similarByProduct(productId: number, topK: number): Promise<RetrievalResponse> {
  const res = await fetch(`${API_BASE}/retrieval/similar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId, top_k: topK, category_filter: [] })
  });
  return parseResponse<RetrievalResponse>(res);
}

export async function similarByImage(file: File, topK: number): Promise<RetrievalResponse> {
  const formData = new FormData();
  formData.append("image", file);
  const res = await fetch(`${API_BASE}/retrieval/similar-image?top_k=${topK}`, {
    method: "POST",
    body: formData
  });
  return parseResponse<RetrievalResponse>(res);
}

export async function textSearch(queryText: string, topK: number): Promise<RetrievalResponse> {
  const res = await fetch(`${API_BASE}/retrieval/text-search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query_text: queryText, top_k: topK, category_filter: [] })
  });
  return parseResponse<RetrievalResponse>(res);
}

export async function photoSearch(file: File, topK: number): Promise<RetrievalResponse> {
  const formData = new FormData();
  formData.append("image", file);
  const res = await fetch(`${API_BASE}/retrieval/photo-search?top_k=${topK}`, {
    method: "POST",
    body: formData
  });
  return parseResponse<RetrievalResponse>(res);
}
