# Running Analytics AI

FastAPI (Python 3.12) + Vite/React 18 (TypeScript) monorepo。
使用 Strava OAuth 登入，串接 Strava API 取得跑步資料，透過 Gemini 提供 AI 分析，SSE 串流回應。
MongoDB 儲存使用者、對話紀錄與 LLM 觀測日誌。

## Monorepo 結構

```
running-analytics-ai/
├── apps/
│   ├── backend/          # FastAPI + Python 3.12
│   │   ├── app/
│   │   │   ├── api/      # router.py（集中路由）
│   │   │   ├── core/     # config, security, dependencies
│   │   │   ├── db/       # mongo.py（Motor async client）
│   │   │   ├── models/   # user, conversation, llm_log
│   │   │   └── services/ # strava, llm, rate_limiter
│   │   └── tests/        # pytest（mongomock-motor）
│   └── frontend/         # Vite + React + TypeScript
│       └── src/
│           ├── api/       # orval 自動生成，勿手動編輯
│           ├── components/
│           ├── pages/     # LoginPage, ActivitiesPage, ActivityDetailPage
│           └── lib/
├── api-contract/
│   └── openapi.json      # API contract 唯一來源
├── tests/
│   └── e2e/              # Playwright E2E 測試
├── docs/superpowers/     # 設計文件與實作計畫
├── docker-compose.base.yml
├── docker-compose.dev.yml
└── Makefile
```

## 啟動主 Docker 服務

```bash
make dev
# 等同於 docker compose -f docker-compose.base.yml -f docker-compose.dev.yml up
```

啟動以下三個服務：

| 服務 | Port | 說明 |
|------|------|------|
| mongodb | 27017 | MongoDB 7 |
| backend | 8000 | FastAPI（uvicorn --reload） |
| frontend | 3000 | Vite dev server |

前置條件：`apps/backend/.env` 需存在（參考 `apps/backend/.env.example`）。

## 啟動 Worktree Docker 服務

每個 worktree 位於 `.worktrees/<name>/`，使用獨立 port 避免與主服務衝突。

**Backend worktree（port 8001）：**
```bash
cd .worktrees/<name>
WORKTREE_PATH=$(pwd) docker compose -f docker-compose.worktree-backend.yml up
```

**Frontend worktree（port 3001）：**
```bash
cd .worktrees/<name>
WORKTREE_PATH=$(pwd) docker compose -f docker-compose.worktree-frontend.yml up
```

| 服務 | Port | Compose 檔案 |
|------|------|-------------|
| worktree backend | 8001 | docker-compose.worktree-backend.yml |
| worktree frontend | 3001 | docker-compose.worktree-frontend.yml |

> 注意：`WORKTREE_PATH` 必須設為該 worktree 的絕對路徑（在 worktree 目錄下執行 `$(pwd)` 即可）。
> 各 worktree 需有自己的 `apps/backend/.env`。

## 執行測試

### 單元測試（Backend）
```bash
make test
# 等同於 cd apps/backend && pytest
```

### Lint 與靜態分析
```bash
make lint
# backend: ruff check + ruff format --check + mypy
# frontend: npm run lint（若 apps/frontend/package.json 存在）
```

### E2E 測試（Playwright）

前置條件：
1. `make dev` 已啟動（backend: http://localhost:8000，frontend: http://localhost:3000）
2. `tests/e2e/.env.e2e` 已設定真實 Strava 測試帳號憑證（參考 `tests/e2e/.env.e2e.example`）

```bash
make test-e2e        # headless 執行
make test-e2e-ui     # 開啟 Playwright UI 模式
```

## API Contract

OpenAPI contract 以 `api-contract/openapi.json` 為唯一來源：

```bash
make generate-api
# 1. curl http://localhost:8000/openapi.json → api-contract/openapi.json
# 2. orval 讀取 openapi.json → 生成 apps/frontend/src/api/（React Query hooks）
```

> 執行前需確保 backend 已啟動。`apps/frontend/src/api/` 為自動生成，勿手動編輯。

## 開發慣例

- **環境變數**：後端讀取 `apps/backend/.env`，欄位參考 `apps/backend/.env.example`（`STRAVA_CLIENT_ID`、`STRAVA_CLIENT_SECRET`、`GEMINI_API_KEY`、`JWT_SECRET`、`ENCRYPTION_KEY`、`MONGODB_URI`）
- **API 異動**：修改後端 API 後需重新執行 `make generate-api` 同步前端 client
- **型別安全**：前端所有 API 呼叫須使用 orval 生成的 hooks，後端維持 mypy strict 模式
- **完整設計文件**：`docs/superpowers/specs/2026-05-22-running-analytics-design.md`（架構決策、API schema、MongoDB schema、LLM 整合細節）

## PR 前必做：OpenSpec 進度同步

**在執行 `gh pr create` 前，必須先確認 OpenSpec 任務進度已更新。**

1. 執行 `git diff main...HEAD --name-only` 確認此次變更的檔案
2. 執行 `find openspec/changes -name tasks.md -not -path '*/archive/*'` 找出所有有效任務清單
3. 讀取每個 `tasks.md`，找出 `- [ ]`（未完成）任務
4. 比對變更檔案，若任務已完成則將 `- [ ]` 改為 `- [x]`
5. 若有修改：`git add openspec/ && git commit -m 'chore(openspec): mark completed tasks before PR'`

> Claude Code 已透過 `.claude/settings.json` 自動執行此檢查。Codex 透過 `.codex/hooks.json` 自動執行。
