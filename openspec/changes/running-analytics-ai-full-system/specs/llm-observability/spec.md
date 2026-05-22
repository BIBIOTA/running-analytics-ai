## ADDED Requirements

### Requirement: LLM 呼叫日誌寫入

系統 SHALL 在每次 LLM 呼叫完成後，無論成功或失敗，都寫入一筆 `llm_logs` 文件，記錄完整的 metadata。

#### Scenario: 成功的 LLM 呼叫

- **WHEN** Gemini API 串流完成並回傳 usage metadata
- **THEN** 系統寫入 `llm_logs` 文件，包含 `request_id`、`user_id`、`conversation_id`、`activity_ids`、`provider_name="google"`、`model_name`、`prompt_version`、`input_tokens`、`output_tokens`、`total_tokens`、`latency_ms`、`status="success"`、`created_at`

#### Scenario: 失敗的 LLM 呼叫

- **WHEN** Gemini API 呼叫在重試後仍失敗
- **THEN** 系統寫入 `llm_logs` 文件，`status` 為 `"error"` 或 `"timeout"`，`error_code` 填入對應錯誤碼，`retry_count` 記錄重試次數

---

### Requirement: LLM Log 唯一請求 ID

系統 SHALL 為每次 `POST /ai/ask` 請求生成唯一 UUID `request_id`，貫穿整個請求生命週期（SSE events、llm_logs）以便追蹤。

#### Scenario: 請求 ID 生成

- **WHEN** 系統收到 `POST /ai/ask`
- **THEN** 生成 UUID v4 作為 `request_id`，同一請求的所有 llm_logs 記錄使用相同 `request_id`

---

### Requirement: LLM Log MongoDB Index

系統 SHALL 在 `llm_logs` 集合上建立 `{ user_id: 1, created_at: -1 }` 複合索引，支援按用戶查詢歷史呼叫記錄。

#### Scenario: Index 建立

- **WHEN** 系統初始化 MongoDB 連線
- **THEN** `db.llm_logs.createIndex({ user_id: 1, created_at: -1 })` 已執行（冪等）

---

### Requirement: Prompt Version 追蹤

系統 SHALL 在 `llm_logs` 的 `prompt_version` 欄位記錄當前使用的 prompt 版本字串，以便日後比較不同版本的效果。

#### Scenario: Prompt 版本寫入

- **WHEN** 系統組裝 prompt 並呼叫 LLM
- **THEN** `llm_logs.prompt_version` 記錄當前 prompt template 的版本字串（如 `"v1.0.0"`）
