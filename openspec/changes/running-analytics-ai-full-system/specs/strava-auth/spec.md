## ADDED Requirements

### Requirement: Strava OAuth Login Redirect

系統 SHALL 提供 `GET /auth/strava` 端點，將用戶重導向至 Strava OAuth 2.0 授權頁面，請求 `activity:read_all` 與 `profile:read_all` scope。

#### Scenario: 用戶點擊登入

- **WHEN** 用戶訪問 `GET /auth/strava`
- **THEN** 系統回傳 HTTP 302，Location 為 Strava OAuth URL，包含正確的 `client_id`、`redirect_uri`、`scope`、`response_type=code`

---

### Requirement: Strava OAuth Callback 與 JWT 發行

系統 SHALL 在 `GET /auth/strava/callback?code=xxx` 中完成 OAuth code exchange，取得 Strava access/refresh token，upsert MongoDB `users` 集合，並發行 HS256 JWT（1 小時到期），最後重導向前端 `/callback?token=xxx`。

#### Scenario: 成功授權

- **WHEN** Strava 回傳有效 `code` 至 callback 端點
- **THEN** 系統向 Strava token endpoint 交換取得 access_token 與 refresh_token，以 AES-256 加密後存入 MongoDB，發行 JWT，重導向前端 `/callback?token=<jwt>`

#### Scenario: Strava 授權被拒

- **WHEN** Strava 回傳 `error=access_denied`
- **THEN** 系統重導向前端 `/login?error=access_denied`

---

### Requirement: Strava Token AES-256 加密儲存

系統 SHALL 以 AES-256 加密 Strava access_token 與 refresh_token 後再存入 MongoDB，解密僅在後端進行，前端永遠無法取得明文 token。

#### Scenario: Token 寫入 DB

- **WHEN** 系統執行 upsert user
- **THEN** `strava_access_token` 與 `strava_refresh_token` 欄位為 AES-256 加密密文，非明文

#### Scenario: Token 讀取用於 API 呼叫

- **WHEN** 系統需呼叫 Strava API
- **THEN** 從 DB 讀取密文後先解密，再用明文 token 發送請求

---

### Requirement: Strava Token 自動 Refresh

系統 SHALL 在每次 Strava API 呼叫前檢查 `strava_token_expires_at`，若距到期不足 5 分鐘則先 refresh token 再呼叫。

#### Scenario: Token 即將到期

- **WHEN** `strava_token_expires_at - now < 5 minutes`
- **THEN** 系統使用 refresh_token 向 Strava 取得新 access_token，更新 DB，再繼續原始 API 呼叫

#### Scenario: Refresh 失敗

- **WHEN** Strava refresh endpoint 回傳 401
- **THEN** 系統回傳 HTTP 401 給前端，前端重導向用戶至 `/login`

---

### Requirement: JWT 驗證中間件

系統 SHALL 對所有受保護端點（`/auth/me`、`/activities/*`、`/ai/*`、`/conversations/*`）驗證 Bearer JWT，無效或過期 token 一律回傳 HTTP 401。

#### Scenario: 有效 JWT

- **WHEN** 請求攜帶有效未過期 Bearer JWT
- **THEN** 系統從 JWT payload 解析 `user_id`，注入 `get_current_user` dependency

#### Scenario: 無效或過期 JWT

- **WHEN** 請求攜帶格式錯誤、簽名無效或已過期的 JWT
- **THEN** 系統回傳 HTTP 401 `{"detail": "Invalid or expired token"}`

---

### Requirement: 取得當前用戶資訊

系統 SHALL 提供 `GET /auth/me` 端點，回傳當前登入用戶的 `display_name` 與 `profile_image_url`。

#### Scenario: 已登入用戶查詢個人資訊

- **WHEN** 已驗證用戶呼叫 `GET /auth/me`
- **THEN** 系統回傳 `{"strava_athlete_id": ..., "display_name": "...", "profile_image_url": "..."}`
