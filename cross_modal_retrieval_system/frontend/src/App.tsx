import { useEffect, useMemo, useState } from "react";

import { listDisplayProducts, photoSearch, similarByImage, similarByProduct, textSearch } from "./api";
import type { ProductDisplayItem, RetrievalItem, RetrievalResponse } from "./types";

type Mode = "similar" | "photo" | "text";

type ProductOption = { id: number; title: string; img: string; description: string };

function makeFallbackImage(title: string, id: number): string {
  const safeTitle = encodeURIComponent(title);
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="600" height="600" viewBox="0 0 600 600">
<defs>
  <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
    <stop offset="0%" stop-color="#1a2332"/>
    <stop offset="100%" stop-color="#243b55"/>
  </linearGradient>
</defs>
<rect width="600" height="600" fill="url(#g)"/>
<circle cx="300" cy="240" r="78" fill="#00d4aa" opacity="0.28"/>
<text x="300" y="390" text-anchor="middle" fill="#e8eaed" font-size="34" font-family="sans-serif">${safeTitle}</text>
<text x="300" y="438" text-anchor="middle" fill="#8b949e" font-size="24" font-family="monospace">ID: ${id}</text>
</svg>`;
  return `data:image/svg+xml;utf8,${svg}`;
}

function resolveImage(payload: Record<string, unknown>, title: string, id: number): string {
  const imageUrl = payload?.image_url;
  if (typeof imageUrl === "string" && imageUrl.trim()) {
    return imageUrl;
  }
  return makeFallbackImage(title, id);
}

function toResultCards(rows: RetrievalItem[]) {
  return rows.map((r) => ({
    id: r.product_id,
    title: (r.payload?.title as string | undefined) ?? `商品 #${r.product_id}`,
    price: (r.payload?.price as string | undefined) ?? "¥--",
    img: resolveImage(r.payload ?? {}, (r.payload?.title as string | undefined) ?? `商品 #${r.product_id}`, r.product_id)
  }));
}

function EmptyState({ msg = "执行检索以查看结果" }: { msg?: string }) {
  return (
    <div className="empty-state">
      <div className="icon">🔍</div>
      <p>{msg}</p>
    </div>
  );
}

function ResultSection({ response }: { response: RetrievalResponse | null }) {
  if (!response) return <EmptyState />;
  const cards = toResultCards(response.results);
  return (
    <>
      <div className="results-header">
        <h3>检索结果 · Top-{cards.length}</h3>
        <span className="latency-badge">P99 延迟: {response.latency_ms} ms</span>
      </div>
      <div className="results-grid">
        {cards.map((p) => (
          <div className="product-card" key={`${p.id}-${p.title}`}>
            <div className="img-wrap">
              <img
                src={p.img}
                alt={p.title}
                onError={(e) => {
                  const img = e.currentTarget;
                  img.onerror = null;
                  img.src = makeFallbackImage(p.title, p.id);
                }}
              />
            </div>
            <div className="info">
              <div className="title">{p.title}</div>
              <div className="price">{p.price}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

export function App() {
  const [mode, setMode] = useState<Mode>("similar");

  const [productOptions, setProductOptions] = useState<ProductOption[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  const [similarUploadFile, setSimilarUploadFile] = useState<File | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState("");
  const [similarPreview, setSimilarPreview] = useState("");
  const [textQuery, setTextQuery] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [similarResponse, setSimilarResponse] = useState<RetrievalResponse | null>(null);
  const [photoResponse, setPhotoResponse] = useState<RetrievalResponse | null>(null);
  const [textResponse, setTextResponse] = useState<RetrievalResponse | null>(null);

  const modeTitle = useMemo(() => {
    if (mode === "similar") return "以图搜图 · 单模态视觉相似检索（SCPH）";
    if (mode === "photo") return "以图搜商品 · 跨模态检索（MIH）";
    return "以文搜商品 · 复杂语义搜索（MIH）";
  }, [mode]);
  const selectedProduct = useMemo(
    () => productOptions.find((p) => p.id === selectedProductId) ?? null,
    [productOptions, selectedProductId]
  );

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const rows = await listDisplayProducts(12);
        if (!alive) return;
        const mapped: ProductOption[] = rows.map((p: ProductDisplayItem) => ({
          id: p.product_id,
          title: p.title || `商品 #${p.product_id}`,
          img: p.image_url || makeFallbackImage(p.title || `商品 #${p.product_id}`, p.product_id),
          description: p.description || ""
        }));
        setProductOptions(mapped);
        if (mapped.length > 0) {
          setSelectedProductId(mapped[0].id);
        }
      } catch (e) {
        if (!alive) return;
        setError(e instanceof Error ? e.message : "加载商品列表失败");
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  function handlePreview(file: File, setter: (v: string) => void) {
    const reader = new FileReader();
    reader.onload = (e) => setter(String(e.target?.result ?? ""));
    reader.readAsDataURL(file);
  }

  async function runSimilarBySelected() {
    setLoading(true);
    setError("");
    try {
      const product = selectedProduct;
      if (!product) {
        throw new Error("请先选择一个商品");
      }
      const ret = await similarByProduct(product.id, 15);
      setSimilarResponse(ret);
    } catch (e) {
      setError(e instanceof Error ? e.message : "检索失败");
    } finally {
      setLoading(false);
    }
  }

  async function runSimilarByUpload() {
    if (!similarUploadFile) return setError("请先上传商品图片");
    setLoading(true);
    setError("");
    try {
      const ret = await similarByImage(similarUploadFile, 15);
      setSimilarResponse(ret);
    } catch (e) {
      setError(e instanceof Error ? e.message : "检索失败");
    } finally {
      setLoading(false);
    }
  }

  async function runPhotoSearch() {
    if (!photoFile) return setError("请先上传图片");
    setLoading(true);
    setError("");
    try {
      const ret = await photoSearch(photoFile, 15);
      setPhotoResponse(ret);
    } catch (e) {
      setError(e instanceof Error ? e.message : "检索失败");
    } finally {
      setLoading(false);
    }
  }

  async function runTextSearch() {
    if (!textQuery.trim()) return setError("请输入查询文本");
    setLoading(true);
    setError("");
    try {
      const ret = await textSearch(textQuery.trim(), 15);
      setTextResponse(ret);
    } catch (e) {
      setError(e instanceof Error ? e.message : "检索失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <header className="header">
        <div className="logo-section">
          <div className="logo-icon">检索</div>
          <div className="logo-text">
            <h1>电商智能检索系统</h1>
            <p>基于 SCPH 与 MIH 的动态哈希检索 · 论文第五章系统展示</p>
          </div>
        </div>
        <div className="model-badges">
          <span className="badge">SCPH</span>
          <span className="badge">MIH</span>
          <span className="badge">64-bit Hash</span>
        </div>
      </header>

      <main className="main-container">
        <div className="tabs">
          <button className={`tab ${mode === "similar" ? "active" : ""}`} onClick={() => setMode("similar")}>相似商品推荐</button>
          <button className={`tab ${mode === "photo" ? "active" : ""}`} onClick={() => setMode("photo")}>拍照购</button>
          <button className={`tab ${mode === "text" ? "active" : ""}`} onClick={() => setMode("text")}>自然语言搜索</button>
        </div>

        <div className={`tab-content ${mode === "similar" ? "active" : ""}`}>
          <div className="search-panel">
            <h3><span className="icon">📷</span> {modeTitle}</h3>
            <p className="panel-desc">当前展示的是 Kafka 增量入库后的商品图片与描述；可直接选中检索相似款</p>
            <div className="product-selector">
              {productOptions.map((p) => (
                <button key={p.id} className={`product-option ${selectedProductId === p.id ? "selected" : ""}`} onClick={() => setSelectedProductId(p.id)}>
                  <img
                    src={p.img}
                    alt={p.title}
                    onError={(e) => {
                      const img = e.currentTarget;
                      img.onerror = null;
                      img.src = makeFallbackImage(p.title, p.id);
                    }}
                  />
                </button>
              ))}
            </div>
            <div className="similar-actions">
              <div className="selected-product-card">
                <div className="selected-product-thumb">
                  <img
                    src={selectedProduct?.img ?? makeFallbackImage("当前选中商品", selectedProductId ?? -1)}
                    alt={selectedProduct?.title ?? "当前选中商品"}
                    onError={(e) => {
                      const img = e.currentTarget;
                      img.onerror = null;
                      img.src = makeFallbackImage(selectedProduct?.title ?? "当前选中商品", selectedProductId ?? -1);
                    }}
                  />
                </div>
                <div className="selected-product-meta">
                  <span>当前选中商品</span>
                  <strong>{selectedProduct?.title ?? "未选择"}</strong>
                  <small>{selectedProduct?.description ?? ""}</small>
                </div>
              </div>
              <div className="similar-primary-actions">
                <button className="btn-search" onClick={runSimilarBySelected} disabled={loading}>检索已选商品相似款</button>
              </div>
              <div className="upload-row">
                <label className="upload-button">
                  上传商品图片推荐
                  <input type="file" accept="image/*" onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) {
                      setSimilarUploadFile(file);
                      handlePreview(file, setSimilarPreview);
                    }
                  }} />
                </label>
                <button className="btn-search" onClick={runSimilarByUpload} disabled={loading}>图片检索推荐</button>
              </div>
              {similarPreview ? <img className="upload-preview show" src={similarPreview} alt="similar preview" /> : null}
            </div>
          </div>
          <div className="results-section"><ResultSection response={similarResponse} /></div>
        </div>

        <div className={`tab-content ${mode === "photo" ? "active" : ""}`}>
          <div className="search-panel">
            <h3><span className="icon">📱</span> {modeTitle}</h3>
            <p className="panel-desc">上传自然场景图片或截屏，系统将在共享汉明空间中召回语义匹配商品</p>
            <div className="upload-zone">
              <label>
                <input type="file" accept="image/*" onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    setPhotoFile(file);
                    handlePreview(file, setPhotoPreview);
                  }
                }} />
                <div className="upload-icon">📤</div>
                <p>拖拽图片到此处，或点击上传</p>
                <p className="hint">支持 JPG、PNG，建议尺寸 224×224</p>
              </label>
              {photoPreview ? <img className="upload-preview show" src={photoPreview} alt="photo preview" /> : null}
            </div>
            <button className="btn-search" onClick={runPhotoSearch} disabled={loading}>开始拍照购检索</button>
          </div>
          <div className="results-section"><ResultSection response={photoResponse} /></div>
        </div>

        <div className={`tab-content ${mode === "text" ? "active" : ""}`}>
          <div className="search-panel">
            <h3><span className="icon">✍️</span> {modeTitle}</h3>
            <p className="panel-desc">输入自然语言描述，系统将跨模态召回符合语义的商品图像</p>
            <div className="text-input-wrapper">
              <textarea value={textQuery} onChange={(e) => setTextQuery(e.target.value)} placeholder="例如：适合秋冬季节搭配大衣的复古风粗跟马丁靴" />
              <button className="btn-search" onClick={runTextSearch} disabled={loading}>检索商品</button>
            </div>
          </div>
          <div className="results-section"><ResultSection response={textResponse} /></div>
        </div>

        {error ? <p className="error-message">{error}</p> : null}
        <p className="footer-note">演示界面 · 基于第五章系统设计 · 实际检索已连接后端 API（相似推荐 / 拍照购 / 自然语言搜索）</p>
      </main>
    </>
  );
}
