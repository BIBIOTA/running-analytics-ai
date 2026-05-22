## ADDED Requirements

### Requirement: AI 問答 SSE 串流端點

系統 SHALL 提供 `POST /ai/ask` 端點，接受 `activity_ids`、`user_message`（最多 500 字）、可選 `conversation_id`，回傳 `text/event-stream` SSE 串流，即時輸出 AI 回應 chunks。

#### Scenario: 成功 SSE 串流回應

- **WHEN** 用戶送出有效問題與 activity_ids
- **THEN** 系統依序回傳 `{"type":"chunk","content":"..."}` 事件，最後回傳 `{"type":"done","conversation_id":"...","usage":{...}}`，客戶端累積 chunks 顯示完整回應

#### Scenario: 用戶訊息超過 500 字

- **WHEN** `user_message` 超過 500 字元
- **THEN** 系統回傳 HTTP 422 Validation Error，不啟動 SSE

#### Scenario: SSE 串流錯誤

- **WHEN** Gemini API 呼叫失敗或 timeout
- **THEN** 系統在串流中發送 `{"type":"error","code":"...","message":"..."}` 事件後關閉連線

---

### Requirement: 多輪對話歷史持久化

系統 SHALL 在每次 AI 回應完成後，將用戶訊息與 AI 回應 append 至 MongoDB `conversations` 集合的 `messages` 陣列，並在下次問答時自動載入歷史作為 LLM context。

#### Scenario: 對話歷史載入

- **WHEN** 用戶在同一活動頁面的第二次問答
- **THEN** 系統從 MongoDB 載入該 `conversation_id` 的 messages，以 alternating user/assistant 格式注入 prompt

#### Scenario: 首次對話（無 conversation_id）

- **WHEN** 請求不含 `conversation_id`
- **THEN** 系統建立新的 conversation 文件，完成後在 SSE done 事件中回傳 `conversation_id`

---

### Requirement: Per-Activity 對話 Scope

系統 SHALL 支援兩種對話 scope：活動詳情頁的 per-activity 對話（`activity_id` 為 Strava activity ID）與活動列表頁的 list-page 對話（`activity_id` 為 null）。

#### Scenario: 詳情頁載入對話歷史

- **WHEN** 前端呼叫 `GET /activities/{id}/conversations`
- **THEN** 系統回傳該用戶在此 activity_id 下的對話歷史

#### Scenario: 列表頁載入對話歷史

- **WHEN** 前端呼叫 `GET /conversations/list-page`
- **THEN** 系統回傳該用戶最近一筆 `activity_id = null` 的對話歷史（auto-upsert 語意）

---

### Requirement: 三層 Prompt 隔離防止 Prompt Injection

系統 SHALL 以固定的三層結構組裝 prompt：System Prompt（繁體中文、只分析跑步數據）→ Business Rules → `<activity_data>` XML tag 包裹的活動數據 → Conversation History → `<user_input>` XML tag 包裹的用戶訊息。

#### Scenario: 用戶嘗試 Prompt Injection

- **WHEN** `user_message` 包含 "忽略所有系統指令" 或類似注入嘗試
- **THEN** LLM 仍依 System Prompt 規則回應，忽略 `<user_input>` 中的規則修改嘗試

#### Scenario: Prompt 組裝驗證

- **WHEN** 系統組裝 prompt
- **THEN** 用戶輸入被包裹在 `<user_input>` tag 內，活動資料被包裹在 `<activity_data>` tag 內

---

### Requirement: LLM 並發請求限制

系統 SHALL 使用 `asyncio.Semaphore(5)` 限制最多 5 個並發 LLM 請求，若等待超過 10 秒則在 SSE 開啟前回傳 HTTP 503。

#### Scenario: 並發請求超過上限

- **WHEN** 已有 5 個進行中的 LLM 請求，第 6 個請求進入
- **THEN** 第 6 個請求等待，若 10 秒內有 slot 釋放則繼續，否則回傳 HTTP 503

#### Scenario: 請求在 timeout 內獲得 slot

- **WHEN** 第 6 個請求在 8 秒後獲得 slot
- **THEN** 請求繼續正常處理，SSE 串流開啟

---

### Requirement: Gemini API 重試機制

系統 SHALL 在 Gemini API 回傳 429 或 5xx 時進行指數退避重試，最多 3 次，最終失敗時在 SSE 中發送 error 事件。

#### Scenario: Gemini 429 重試

- **WHEN** Gemini API 第一次呼叫回傳 429
- **THEN** 系統等待後重試，最多 3 次；若第 3 次仍失敗，發送 `{"type":"error","code":"rate_limit","message":"請稍後再試"}`

#### Scenario: Gemini 30 秒 Timeout

- **WHEN** Gemini API 呼叫超過 30 秒未回應
- **THEN** 系統取消請求，發送 `{"type":"error","code":"timeout","message":"回應逾時，請稍後再試"}`，並記錄 `status=timeout` 至 llm_logs
