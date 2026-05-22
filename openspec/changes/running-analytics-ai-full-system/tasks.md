## 1. 專案基礎建設 (Monorepo + Docker)

- [x] 1.1 建立 monorepo 目錄結構：`apps/frontend`、`apps/backend`、`api-contract`、`docs`
- [x] 1.2 建立根目錄 `package.json`（npm workspaces）
- [x] 1.3 撰寫 `docker-compose.yml`（frontend:3000、backend:8000、mongodb:27017）
- [x] 1.4 撰寫 `docker-compose.override.yml`（uvicorn --reload、Vite dev mode）
- [x] 1.5 撰寫 `Makefile`：`dev`、`lint`、`test`、`generate-api` targets
- [x] 1.6 建立 `apps/backend/.env.example`，列出所有必填 env vars

## 2. 後端基礎框架 (FastAPI + MongoDB)

- [x] 2.1 建立 `apps/backend/pyproject.toml`（fastapi、motor、pydantic-settings、python-jose、cryptography、google-generativeai、ruff、mypy、pytest、pytest-asyncio、httpx、mongomock-motor）
- [x] 2.2 實作 `app/main.py`：FastAPI app 建立、CORS middleware（允許 localhost:3000）、router 掛載、lifespan event
- [x] 2.3 實作 `app/core/config.py`：Pydantic Settings 讀取 `STRAVA_CLIENT_ID`、`STRAVA_CLIENT_SECRET`、`GEMINI_API_KEY`、`MONGODB_URI`、`JWT_SECRET`、`ENCRYPTION_KEY`、`FRONTEND_URL`
- [x] 2.4 實作 `app/db/mongo.py`：Motor async client singleton，collection accessors（users、conversations、llm_logs），啟動時建立 indexes
- [x] 2.5 實作 `app/models/user.py`、`conversation.py`、`llm_log.py` Pydantic 模型

## 3. 認證：Strava OAuth + JWT

- [ ] 3.1 實作 `app/core/security.py`：HS256 JWT encode/decode（1 小時到期）；AES-256 encrypt/decrypt（用於 Strava tokens）
- [ ] 3.2 實作 `app/core/dependencies.py`：`get_current_user` FastAPI dependency（驗證 Bearer JWT，載入 MongoDB user）
- [ ] 3.3 實作 `app/api/auth.py`：`GET /auth/strava`（OAuth redirect）、`GET /auth/strava/callback`（code exchange、upsert user、發行 JWT、重導向前端）、`GET /auth/me`
- [ ] 3.4 實作 `app/services/strava.py`：`exchange_code()`、`refresh_token_if_needed()`（檢查 expires_at 5 分鐘）、`get_activities()`、`get_activity_detail()`、`get_activity_streams()`
- [ ] 3.5 撰寫 `tests/test_auth.py`：JWT round-trip 測試、OAuth callback 流程測試（httpx + mongomock-motor）

## 4. 活動 API

- [ ] 4.1 實作 `app/api/activities.py`：`GET /activities`（僅 Run type，最近 30 筆）、`GET /activities/{id}`（含 gpx_stream_url）、`GET /activities/{id}/conversations`（per-activity 對話歷史）
- [ ] 4.2 在 activities 端點加入活動所有權驗證（IDOR 防護）
- [ ] 4.3 撰寫 `tests/test_activities.py`：列表、詳情、IDOR 測試

## 5. AI 問答：LLM 服務 + SSE

- [ ] 5.1 實作 `app/services/rate_limiter.py`：`LLMRateLimiter`（asyncio.Semaphore(5)，timeout 10s），app lifespan 建立單一 instance
- [ ] 5.2 實作 `app/services/llm.py`：`assemble_prompt()`（三層隔離：system、business rules、`<activity_data>`、conversation history、`<user_input>`）
- [ ] 5.3 實作 `app/services/llm.py`：`stream_gemini_response()`（Gemini streaming API、指數退避重試 max 3 次、30s timeout、SSE chunk 生成）
- [ ] 5.4 實作 `app/services/llm.py`：`persist_conversation()`（append messages 至 conversations 集合，upsert list-page 語意）、`write_llm_log()`
- [ ] 5.5 實作 `app/api/ai.py`：`POST /ai/ask`（validate → rate limit → load history → fetch activities → assemble prompt → SSE stream → persist → log）
- [ ] 5.6 實作 `GET /conversations/list-page`（回傳用戶最近一筆 activity_id=null 對話）
- [ ] 5.7 撰寫 `tests/test_rate_limiter.py`：並發限制、timeout 行為
- [ ] 5.8 撰寫 `tests/test_llm.py`：prompt 組裝驗證（injection 防護）、Gemini retry 邏輯（mock）
- [ ] 5.9 撰寫 `tests/test_ai_endpoint.py`：SSE integration test（httpx AsyncClient）

## 6. OpenAPI Contract 匯出

- [ ] 6.1 在 `app/main.py` 加入啟動時將 `/openapi.json` 寫入 `api-contract/openapi.json` 的邏輯（或 `make generate-api` 觸發 `curl localhost:8000/openapi.json`）
- [ ] 6.2 驗證 `api-contract/openapi.json` 完整包含所有端點與 schema

## 7. 前端基礎框架 (Vite + React + orval)

- [x] 7.1 建立 `apps/frontend`（`npm create vite` TypeScript + React 18）
- [x] 7.2 安裝依賴：shadcn/ui、Tailwind CSS、React Router v6、React Query（tanstack）、leaflet、leaflet-gpx、orval
- [x] 7.3 設定 `vite.config.ts`（proxy `/api` → `localhost:8000`）
- [x] 7.4 設定 orval config，指向 `api-contract/openapi.json`，輸出至 `src/api/`
- [x] 7.5 執行 `make generate-api`，確認 `src/api/` 生成正確 typed hooks

## 8. 前端路由 + 認證 Hook

- [ ] 8.1 實作 `src/hooks/useAuth.ts`：JWT localStorage 管理、讀取 `/auth/me`、logout（清除 token）、401 自動導向 `/login`
- [ ] 8.2 實作 `src/router.tsx`：React Router v6 路由設定，ProtectedRoute wrapper（無 JWT → 重導向 `/login`），`/callback` token 處理邏輯

## 9. 前端頁面實作（依 Figma 設計稿）

> **重要**: 實作每個頁面前，MUST 先透過 Figma MCP 查詢設計稿：
> - `mcp__plugin_figma_figma__get_design_context` — 取得元件規格與 tokens
> - `mcp__plugin_figma_figma__get_screenshot` — 確認視覺設計
>
> 需由設計師提供 Figma file key 與各頁面 node-id。

- [ ] 9.1 查詢 Figma 設計稿：取得 LoginPage 的 file key + node-id，呼叫 Figma MCP 取得設計規格
- [ ] 9.2 實作 `src/pages/LoginPage.tsx`：Strava OAuth 登入按鈕，依 Figma 設計稿
- [ ] 9.3 查詢 Figma 設計稿：取得 ActivitiesPage 的設計規格（列表 + AI 面板）
- [ ] 9.4 實作 `src/components/ActivityCard.tsx`：活動卡片（日期、距離、配速、時間），依 Figma 設計稿
- [ ] 9.5 實作 `src/pages/ActivitiesPage.tsx`：活動列表渲染（orval hook）+ skeleton loading，依 Figma 設計稿
- [ ] 9.6 查詢 Figma 設計稿：取得 ActivityDetailPage 的設計規格（指標 + 地圖 + AI 面板）
- [ ] 9.7 實作 `src/components/ActivityMap.tsx`：Leaflet + leaflet-gpx 地圖元件（GPS 無資料時隱藏）
- [ ] 9.8 實作 `src/pages/ActivityDetailPage.tsx`：完整活動指標 + ActivityMap，依 Figma 設計稿

## 10. AI 問答前端元件

- [ ] 10.1 實作 `src/hooks/useSSE.ts`：fetch + ReadableStream SSE 解析，狀態機（idle/connecting/streaming/done/error），AbortController 清理
- [ ] 10.2 實作 `src/hooks/useConversation.ts`：載入對話歷史（per-activity 或 list-page），SSE 完成後 append 新訊息
- [ ] 10.3 查詢 Figma 設計稿：取得 AiChat 面板的設計規格
- [ ] 10.4 實作 `src/components/AiChat.tsx`：多輪對話 UI、SSE 串流顯示（chunk 即時 append）、預設 prompt、錯誤狀態，依 Figma 設計稿
- [ ] 10.5 將 AiChat 面板整合至 ActivitiesPage（list-page scope）
- [ ] 10.6 將 AiChat 面板整合至 ActivityDetailPage（per-activity scope）

## 11. 前端測試

- [ ] 11.1 設定 Vitest + React Testing Library
- [ ] 11.2 撰寫 `useSSE.test.ts`：EventSource mock、狀態轉換（idle→connecting→streaming→done）、error 狀態
- [ ] 11.3 撰寫 `useAuth.test.ts`：JWT 過期偵測、logout 清除、401 重導向
- [ ] 11.4 撰寫 `AiChat.test.tsx`：SSE chunk 渲染、error 狀態顯示

## 12. 靜態分析設定

- [ ] 12.1 設定後端 `ruff`（linting + import sorting）+ `mypy`（strict mode）
- [ ] 12.2 設定前端 `ESLint`（react-hooks、typescript-eslint rules）+ `Prettier`
- [ ] 12.3 在 `Makefile lint` target 中串接所有 linting 工具
- [ ] 12.4 執行 `make lint` 確認零錯誤

## 13. 端對端驗證

- [ ] 13.1 執行 `make dev`，確認 docker-compose 三個服務全部啟動
- [ ] 13.2 完整走過 Strava OAuth 登入流程，確認 JWT 正確發行並存入 localStorage
- [ ] 13.3 驗證活動列表頁顯示正確，AI 問答面板 SSE 串流正常
- [ ] 13.4 驗證活動詳情頁 Leaflet 地圖渲染正確，per-activity AI 對話歷史持久化
- [ ] 13.5 執行 `make test` 確認全部測試通過
