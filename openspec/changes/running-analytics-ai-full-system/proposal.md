## Why

跑者記錄了大量 Strava 運動數據，卻缺乏能主動分析並給予個人化建議的工具。本系統將 Strava OAuth 登入、活動瀏覽與 AI 對話整合為一個本地可運行的 Web 應用，讓跑者能直接對自己的數據提問並獲得即時洞察。

## What Changes

- 新增 Strava OAuth 登入流程，後端發行 JWT session
- 新增活動列表頁（近期跑步紀錄：距離、配速、時間）
- 新增活動詳情頁（完整指標 + Leaflet GPX 地圖）
- 新增 AI 問答面板，支援多輪對話與 SSE 串流回應
- 對話歷史按活動維度持久化儲存於 MongoDB
- 後端完全掌控 LLM API Key 與模型選擇，前端不暴露
- 三層 Prompt 隔離設計防範 Prompt Injection
- llm_logs 集合記錄每次 LLM 呼叫的 tokens、延遲、狀態
- Docker Compose 本地一鍵啟動（frontend + backend + MongoDB）
- 前端 UI 依照 Figma 設計稿實作（設計稿透過 Figma MCP 查詢）

## Capabilities

### New Capabilities

- `strava-auth`: Strava OAuth 2.0 登入、JWT session 管理、token AES-256 加密儲存、自動 refresh
- `activities`: 從 Strava API 取得活動列表與詳情，包含 GPX stream URL
- `ai-chat`: 多輪 AI 對話（per-activity 與 list-page 兩種 scope），SSE 串流，Prompt 注入防護
- `llm-observability`: llm_logs 集合，記錄每次 LLM 呼叫的完整 metadata
- `frontend-ui`: React 18 + Vite 前端，依 Figma 設計稿實作（LoginPage、ActivitiesPage、ActivityDetailPage + AiChat 面板）

### Modified Capabilities

<!-- No existing capabilities - this is a greenfield system -->

## Impact

- **Backend**: FastAPI Python 3.12 app；新增 `auth`, `activities`, `ai` router；`services/strava.py`, `services/llm.py`, `services/rate_limiter.py`；Motor async MongoDB client
- **Frontend**: Vite + React 18 TypeScript；orval 自動生成 typed API client；shadcn/ui + Tailwind；Leaflet GPX 地圖
- **API Contract**: `api-contract/openapi.json` 作為前後端合約 single source of truth；`make generate-api` 觸發 orval codegen
- **Database**: MongoDB collections — `users`, `conversations`, `llm_logs`
- **Dependencies**: Google Gemini API（gemini-3.1-pro-preview）、Strava API
- **Infrastructure**: Docker Compose（frontend:3000, backend:8000, mongodb:27017）
