## 1. 模型更新

- [ ] 1.1 在 `apps/backend/app/models/llm_log.py` 的 `LlmLog` 新增 `reasoning_tokens: int | None = None` 欄位，位置在 `total_tokens` 之後

## 2. 測試更新

- [ ] 2.1 在 `apps/backend/tests/test_backend_infrastructure.py` 的 `test_user_conversation_and_llm_log_models_serialize` 測試中，為 `LlmLog` 加入 `reasoning_tokens=500` 並驗證序列化結果
- [ ] 2.2 新增一個測試案例，驗證 `reasoning_tokens=None` 時序列化仍正常
