## Context

這是一個 greenfield 全端系統，目標讓跑者能透過 Strava OAuth 登入後瀏覽活動數據並與 AI 對話獲得訓練建議。技術棧為 TypeScript React 前端 + Python FastAPI 後端 + MongoDB，以 Docker Compose 本地部署。前端 UI 須依照 Figma 設計稿實作——設計稿由設計師在 Figma 中維護，實作前透過 **Figma MCP** (`get_design_context`、`get_screenshot`) 查詢最新設計。

## Goals / Non-Goals

**Goals:**
- OpenAPI contract 作為前後端唯一合約來源（`api-contract/openapi.json`）
- JWT + AES-256 保護用戶 token，不在前端暴露 Gemini API Key
- SSE 串流讓 AI 回應即時呈現
- 每次 LLM 呼叫完整記錄於 `llm_logs`
- asyncio Semaphore 限制最多 5 個並發 LLM 請求
- 三層 Prompt 隔離防範 Prompt Injection
- 前端 UI 完全依照 Figma 設計稿，禁止自由發揮

**Non-Goals:**
- 生產部署（無 Redis、無 CDN、無 HTTPS 終止）
- 多 LLM provider 或 fallback 模型
- 社交功能或多用戶協作
- 行動 App

## Decisions

### D1: OpenAPI-first Contract Flow

**決策**: FastAPI 啟動時匯出 `/openapi.json` → 寫入 `api-contract/openapi.json` → orval 生成前端 typed hooks。

**理由**: 確保前後端型別永遠同步，消除手動對齊成本。orval 基於 React Query，與 shadcn/ui 生態整合良好。

**替代方案**: 手寫 SDK（維護成本高）、GraphQL（overkill for this scale）。

---

### D2: JWT Session + AES-256 Token Storage

**決策**: 後端在 Strava OAuth callback 時發行 HS256 JWT（1 小時）；Strava access/refresh token 以 AES-256 加密後存 MongoDB。

**理由**: Strava token 是用戶最敏感資產，明文存 DB 是不可接受的風險。JWT 讓前端無狀態，避免 session store 依賴。

**替代方案**: httpOnly cookie（需要 CSRF 防護）、opaque token（需要 DB 查詢）。

---

### D3: SSE 而非 WebSocket

**決策**: LLM 串流採用 Server-Sent Events（`POST /ai/ask` 回傳 `text/event-stream`）。

**理由**: LLM 串流是單向（server → client），SSE 比 WebSocket 更輕量且天然支援 HTTP/1.1 proxy。`EventSource` 有標準瀏覽器 API，但因需要 POST body，改用 `fetch` + `ReadableStream` 手動解析 SSE。

**替代方案**: WebSocket（雙向 overkill）、long polling（高延遲）。

---

### D4: 嵌入式 messages vs 獨立 Message Collection

**決策**: `conversations.messages` 採嵌入陣列，不拆獨立 collection。

**理由**: 每次查詢都需要完整對話歷史，嵌入避免 join，符合 MongoDB document model 最佳實踐。每個 conversation 預估 messages 數量有限（< 100 輪）。

**替代方案**: 獨立 `messages` collection（join 成本，無必要複雜度）。

---

### D5: 前端 UI 依 Figma 設計稿實作

**決策**: 前端元件（LoginPage、ActivitiesPage、ActivityDetailPage、AiChat）在實作前**必須**透過 Figma MCP 查詢設計稿，不得自行決定視覺設計。

**理由**: 確保設計一致性，避免工程師自行解讀造成偏差。Figma MCP 提供 `get_design_context` 和 `get_screenshot` 可直接在 Claude Code 中查詢。

**實作流程**:
1. 呼叫 `mcp__plugin_figma_figma__get_design_context` 取得元件規格
2. 呼叫 `mcp__plugin_figma_figma__get_screenshot` 確認視覺效果
3. 依規格實作，使用 shadcn/ui 元件 + Tailwind CSS tokens

---

### D6: asyncio Semaphore Rate Limiter

**決策**: 單一 `asyncio.Semaphore(5)` 限制並發 LLM 請求，timeout 10 秒。

**理由**: 單 process 開發環境足夠；比 Redis 輕量，無外部依賴。

**替代方案**: Redis + token bucket（生產環境再升級）。

---

### D7: 三層 Prompt 隔離

**決策**: System → Business Rules → Activity Data（XML tag 包裹）→ Conversation History → User Input（XML tag 包裹）。

**理由**: XML tag 隔離讓 LLM 能明確區分受信任指令與用戶輸入，防止 Prompt Injection。System prompt 明確指示忽略 `<user_input>` 中的規則修改嘗試。

### D8: 前端共用元件設計

**決策**: 從 Figma 設計稿提取 6 個共用元件（`AppHeader`、`MetricItem`、`MetricCard`、`ActivityTag`、`ChatMessage`、`AiChatPanel`），採扁平結構放置於 `src/components/`，`ChatMessage` 獨立匯出（非封裝於 AiChatPanel 內部）。

**理由**: `MetricItem`（Activity Card 用，無 icon，value 18px）與 `MetricCard`（Detail Grid 用，有 icon，value 22px，帶顏色）視覺結構差異明顯，用兩個獨立元件比單一元件加 `size` prop 更清晰。`ChatMessage` 獨立匯出便於單獨測試及未來擴充。

**Figma 參照**:
- 設計稿 file key: `aXWF4fYRx5vUg1JIEyPlNx`
- Activities Page node: `3:2`（Figma page `3:2`，frame `8:2`）
- Activity Detail Page node: `3:3`（Figma page `3:3`，frame `15:2`）
- App Header Figma symbol: node `26:2`（instance `28:2` 在 Detail Page）

**MetricCard value 顏色**（從 Figma 直接取值）:

| Metric | valueColor |
|--------|-----------|
| 距離 | `#f97316` |
| 配速 | `#22c55e` |
| 時間 | `#5e98f8` |
| 心率 | `#ef4444` |
| 爬升 | `#d0ab18` |
| 熱量 | `#f97316` |

**ActivityTag**: 所有類型共用同一樣式（`rgba(249,115,22,0.15)` 背景 + `#f97316` 文字），不需要 variant prop。

**完整 spec**: `docs/superpowers/specs/2026-05-22-shared-components-design.md`

**替代方案**: 單一 `MetricDisplay` 元件加 `size="sm|lg"` prop（API 較複雜，YAGNI 考量下捨棄）；AiChatPanel 封裝所有子元件（減少測試彈性，捨棄）。

---

## Risks / Trade-offs

- **Strava token 加密 key 遺失** → 所有用戶需重新授權。緩解：`ENCRYPTION_KEY` 存於 `.env`，禁止 commit。
- **JWT 無法撤銷** → 1 小時內 token 外洩有效。緩解：1 小時短期限；生產環境加 refresh token rotation。
- **SSE 透過 POST 需 fetch 手動解析** → 不能直接用 `EventSource` API。緩解：`useSSE` hook 封裝 fetch + ReadableStream 邏輯。
- **Gemini model 名稱變動** → `gemini-3.1-pro-preview` 可能下線。緩解：model 名從 `core/config.py` 的 env var 讀取。
- **mongomock-motor 與真實 Motor 行為差異** → 測試通過但 prod 失敗。緩解：整合測試用真實 MongoDB container（pytest fixture）。
- **Figma 設計稿未完成時前端被 block** → 緩解：可先用 skeleton/placeholder 元件，等設計稿就緒後補齊細節。

## Open Questions

- ~~Figma 設計稿 file key 與各 page 的 node-id 為何？~~ **已解決**：file key `aXWF4fYRx5vUg1JIEyPlNx`；Login Page `0:1`、Activities Page `3:2`、Activity Detail Page `3:3`。
- `gemini-3.1-pro-preview` 是否為最終 model ID？需在 Gemini API 文件確認。
- List-page conversation 的「最新一筆」語意：是否需要讓用戶手動開新對話？（目前設計為 auto-upsert 最新一筆）
