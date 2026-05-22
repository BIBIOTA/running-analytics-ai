## Context

`LlmLog` 是後端記錄每次 LLM 呼叫的資料模型，目前有 `input_tokens`、`output_tokens`、`total_tokens` 三個欄位。Gemini API 在啟用 thinking 模式時，`usageMetadata` 會額外回傳 `thoughtsTokenCount`，且此值已計入 `totalTokenCount`，因此 `total_tokens ≠ input_tokens + output_tokens`。若不記錄 `reasoning_tokens`，就無法拆解成本或分析推理使用量。

## Goals / Non-Goals

**Goals:**
- 在 `LlmLog` 新增 `reasoning_tokens: int | None = None` 欄位
- 更新測試以涵蓋新欄位

**Non-Goals:**
- 修改 MongoDB 既有資料（欄位為 optional，舊文件自然為 null）
- 實作實際的 Gemini API 呼叫或 token 填入邏輯（屬後續 LLM service 層的範疇）

## Decisions

**欄位型別選 `int | None`**：與既有 token 欄位保持一致；thinking 未啟用時 API 不回傳此值，故 nullable 是正確設計。

**不新增 MongoDB index**：`reasoning_tokens` 不會作為查詢條件，無需 index。

**不修改 `total_tokens`**：`total_tokens` 直接映射 API 的 `totalTokenCount`（已包含 thoughts），維持與 API 回傳值的 1:1 對應，避免在應用層重新計算造成誤差。

## Risks / Trade-offs

- `thoughtsTokenCount` 在部分 Gemini 模型版本（如 gemini-3-flash-preview）有回報不回傳的問題 → 欄位設計為 nullable 已涵蓋此情況，無需額外處理
