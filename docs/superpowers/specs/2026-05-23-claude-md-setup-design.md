# CLAUDE.md Setup Design

**Date:** 2026-05-23
**Scope:** 新增 CLAUDE.md 並 symlink 至 AGENTS.md

---

## 目標

為 AI agent（Claude Code、Gemini、Copilot 等）建立一份精簡的專案快速參考文件，包含：
- 專案架構概覽
- 啟動主 Docker 服務的方式
- 啟動 Worktree Docker 服務的方式
- 執行測試的方式（單元測試 + Lint + E2E）
- API Contract 更新流程
- 開發慣例

建立後將 `CLAUDE.md` symlink 為 `AGENTS.md`，使 Gemini 等 agent 也能讀取相同內容。

---

## CLAUDE.md 內容設計

### 1. 專案概覽

一段話說明技術棧：FastAPI + Vite/React 18 monorepo，Strava OAuth，Gemini AI，SSE 串流，MongoDB。

### 2. Monorepo 結構

精簡目錄樹，標示各目錄用途：
- `apps/backend/app/` — FastAPI 模組（api、core、db、models、services）
- `apps/frontend/src/api/` — orval 自動生成，勿手動編輯
- `api-contract/openapi.json` — API contract 唯一來源
- `tests/e2e/` — Playwright E2E 測試

### 3. 啟動主 Docker 服務

- `make dev`（`docker compose up`）
- 三個服務：mongodb:27017、backend:8000、frontend:3000
- 前置條件：`apps/backend/.env` 需存在

### 4. 啟動 Worktree Docker 服務

- Backend worktree：`WORKTREE_PATH=$(pwd) docker compose -f docker-compose.backend-local.yml up`（port 8001）
- Frontend worktree：`WORKTREE_PATH=$(pwd) docker compose -f docker-compose.frontend-worktree.yml up`（port 3001）
- `WORKTREE_PATH` 必須設為 worktree 的絕對路徑

### 5. 執行測試

- 單元測試：`make test`（pytest）
- Lint：`make lint`（ruff + mypy + eslint）
- E2E：`make test-e2e` / `make test-e2e-ui`（需先啟動 docker + 設定 `.env.e2e`）

### 6. API Contract

- `make generate-api`：匯出 openapi.json → orval 生成前端 client
- 需先啟動 backend

### 7. 開發慣例

- `.env` 欄位參考 `.env.example`
- API 異動後需重跑 `make generate-api`
- 前端 API 呼叫用 orval hooks，後端維持 mypy strict

---

## 後置動作

建立 symlink：`AGENTS.md -> CLAUDE.md`

---

## 不在範圍內

- 修改現有程式碼
- 新增 worktree 管理腳本
- 更改 Makefile
