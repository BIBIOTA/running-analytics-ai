## ADDED Requirements

### Requirement: 前端 UI 依 Figma 設計稿實作

前端所有頁面與元件 SHALL 依照 Figma 設計稿實作，禁止自行決定視覺設計。實作前 MUST 透過 **Figma MCP** 查詢最新設計規格。

**Figma MCP 查詢方式（在 Claude Code 中執行）**:
- `mcp__plugin_figma_figma__get_design_context` — 取得元件規格、間距、顏色 tokens
- `mcp__plugin_figma_figma__get_screenshot` — 截取頁面視覺截圖確認設計意圖

**查詢前需取得**: Figma file key 與各頁面/元件的 node-id（由設計師提供或在 Figma URL 中解析）。

#### Scenario: 開始實作新頁面

- **WHEN** 工程師開始實作任一頁面（LoginPage、ActivitiesPage、ActivityDetailPage）
- **THEN** MUST 先呼叫 Figma MCP 取得該頁面的設計規格，再依規格實作，不得自行假設視覺設計

#### Scenario: 設計稿更新後重新實作

- **WHEN** 設計師更新 Figma 設計稿
- **THEN** 工程師重新呼叫 Figma MCP 取得最新規格，更新實作

---

### Requirement: LoginPage

系統 SHALL 提供 `/login` 頁面，顯示 Strava OAuth 登入按鈕，點擊後導向 `GET /auth/strava`。

#### Scenario: 用戶點擊 Strava 登入

- **WHEN** 用戶點擊登入按鈕
- **THEN** 瀏覽器導向後端 `GET /auth/strava`，開始 OAuth 流程

#### Scenario: 未登入用戶訪問保護頁面

- **WHEN** 未攜帶有效 JWT 的用戶訪問 `/activities` 或 `/activities/:id`
- **THEN** React Router 自動重導向至 `/login`

---

### Requirement: OAuth Callback Token 處理

系統 SHALL 在前端 `/callback` 路由解析 URL 中的 `?token=xxx`，存入 `localStorage`，並重導向至 `/activities`。

#### Scenario: 成功 OAuth 回調

- **WHEN** 後端重導向至 `/callback?token=<jwt>`
- **THEN** 前端提取 token 存入 `localStorage["jwt"]`，移除 URL token 參數，跳轉至 `/activities`

---

### Requirement: ActivitiesPage 活動列表

系統 SHALL 提供 `/activities` 頁面，顯示最近跑步活動列表，每筆顯示日期時間、距離、配速、總時間。點擊任一活動導向 `/activities/:id`。

#### Scenario: 活動列表渲染

- **WHEN** 用戶訪問 `/activities`
- **THEN** 頁面呼叫 orval 生成的 hook 取得活動列表，以卡片形式顯示每筆活動的核心指標

#### Scenario: 活動列表 Loading 狀態

- **WHEN** API 請求進行中
- **THEN** 頁面顯示 skeleton loading 狀態（依 Figma 設計稿）

---

### Requirement: ActivitiesPage AI 問答面板

`/activities` 頁面 SHALL 包含可收合的 AI 問答面板（sidebar 或 panel，依 Figma 設計稿），預設 prompt 為「分析我近一個月的跑步活動」，支援自由輸入與多輪對話。

#### Scenario: 使用預設 Prompt 問答

- **WHEN** 用戶點擊「分析我近一個月的跑步活動」送出
- **THEN** 系統呼叫 `POST /ai/ask` 並以 SSE 即時顯示串流回應

#### Scenario: 多輪對話

- **WHEN** 用戶在同一 session 連續提問
- **THEN** 前端載入並顯示完整對話歷史，每次回應 append 至對話記錄

---

### Requirement: ActivityDetailPage 活動詳情

系統 SHALL 提供 `/activities/:id` 頁面，顯示完整活動指標（距離、配速、心率、海拔、分段）與 Leaflet GPX 地圖。

#### Scenario: 地圖渲染

- **WHEN** 活動含 GPS 資料（`gpx_stream_url` 非 null）
- **THEN** 頁面以 `leaflet` + `leaflet-gpx` 渲染 GPX 路線於地圖上

#### Scenario: 無 GPS 資料

- **WHEN** `gpx_stream_url` 為 null
- **THEN** 頁面隱藏地圖區塊，僅顯示文字指標

---

### Requirement: ActivityDetailPage AI 問答面板

`/activities/:id` 頁面 SHALL 包含 AI 問答面板，預設 prompt 為「分析這次跑步活動」，對話歷史從 `GET /activities/{id}/conversations` 載入，支援多輪 + SSE 串流。

#### Scenario: 詳情頁對話歷史載入

- **WHEN** 用戶訪問 `/activities/:id`
- **THEN** `useConversation` hook 呼叫 API 載入該活動的對話歷史，渲染於 AI 問答面板

---

### Requirement: useSSE Hook

前端 SHALL 提供 `useSSE` hook，封裝 `fetch` + `ReadableStream` 解析 SSE 邏輯，管理 `idle/connecting/streaming/done/error` 狀態機，元件卸載時自動 abort。

#### Scenario: SSE 串流累積

- **WHEN** SSE 串流進行中
- **THEN** `useSSE.content` 隨每個 chunk 即時累積，UI 即時更新顯示進度中的回應

#### Scenario: 元件卸載清理

- **WHEN** 用戶在串流進行中離開頁面
- **THEN** `useSSE` 呼叫 `AbortController.abort()`，停止 fetch 請求

---

### Requirement: orval 生成 Typed API Client

前端所有 API 呼叫 SHALL 使用 orval 從 `api-contract/openapi.json` 自動生成的 typed hooks，禁止手寫 API 呼叫。

#### Scenario: API 合約更新後重新生成

- **WHEN** 後端修改 API 並更新 `api-contract/openapi.json`
- **THEN** 執行 `make generate-api`，前端 `src/api/` 目錄自動更新，TypeScript 型別錯誤提示 breaking changes

---

### Requirement: CORS 配置

後端 SHALL 設定 CORS，僅允許前端 origin（`http://localhost:3000`）存取，不允許其他 origin。

#### Scenario: 合法前端請求

- **WHEN** 來自 `http://localhost:3000` 的請求
- **THEN** 後端回應包含正確 `Access-Control-Allow-Origin` header

#### Scenario: 非法 origin 請求

- **WHEN** 來自其他 origin 的請求
- **THEN** 後端不回傳 `Access-Control-Allow-Origin`，瀏覽器阻止請求
