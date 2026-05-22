## Why

Gemini 2.5 系列模型啟用 thinking 模式時，API 回傳的 `totalTokenCount` 包含 `thoughtsTokenCount`（推理過程 token），導致 `total_tokens ≠ input_tokens + output_tokens`。目前 `LlmLog` 模型缺少此欄位，無法正確追蹤思考 token 的用量，影響成本分析與效能調校。

## What Changes

- 在 `LlmLog` Pydantic 模型新增 `reasoning_tokens: int | None = None` 欄位，對應 Gemini API 的 `thoughtsTokenCount`
- 更新對應的測試，驗證新欄位的序列化行為

## Capabilities

### New Capabilities

- `llm-log-thoughts-tokens`: 在 LLM 呼叫日誌中記錄 Gemini thinking 模式的推理 token 數量

### Modified Capabilities

（無現有 spec 需要修改）

## Impact

- `apps/backend/app/models/llm_log.py`：新增欄位
- `apps/backend/tests/test_backend_infrastructure.py`：更新模型序列化測試
