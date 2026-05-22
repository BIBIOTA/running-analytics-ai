## ADDED Requirements

### Requirement: LlmLog records thinking token count
`LlmLog` 模型 SHALL 包含 `reasoning_tokens: int | None` 欄位，用以記錄 Gemini API `usageMetadata.thoughtsTokenCount` 的值。未啟用 thinking 模式時，該欄位 SHALL 為 `None`。

#### Scenario: thinking 模式啟用時記錄思考 token
- **WHEN** LLM 呼叫使用 Gemini thinking 模式且 API 回傳 `thoughtsTokenCount`
- **THEN** `LlmLog.reasoning_tokens` SHALL 儲存該整數值

#### Scenario: thinking 模式未啟用時欄位為 None
- **WHEN** LLM 呼叫未使用 thinking 模式，API 不回傳 `thoughtsTokenCount`
- **THEN** `LlmLog.reasoning_tokens` SHALL 為 `None`

#### Scenario: LlmLog 序列化包含 reasoning_tokens 欄位
- **WHEN** 對 `LlmLog` 物件呼叫 `model_dump()`
- **THEN** 輸出字典 SHALL 包含 `reasoning_tokens` 鍵，值為整數或 `None`
