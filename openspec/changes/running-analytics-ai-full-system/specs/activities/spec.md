## ADDED Requirements

### Requirement: 取得近期跑步活動列表

系統 SHALL 提供 `GET /activities` 端點，回傳當前用戶最近的跑步活動列表（僅 `type=Run`），每筆包含 `id`、`name`、`start_date`、`distance`、`moving_time`、`average_speed`（配速）、`total_elevation_gain`。

#### Scenario: 成功取得活動列表

- **WHEN** 已驗證用戶呼叫 `GET /activities`
- **THEN** 系統呼叫 Strava API，過濾 `type=Run`，回傳陣列，預設最近 30 筆

#### Scenario: 用戶無任何跑步活動

- **WHEN** Strava API 回傳空陣列
- **THEN** 系統回傳空陣列 `[]`，HTTP 200

#### Scenario: Strava API 呼叫失敗

- **WHEN** Strava API 回傳 5xx 或 timeout
- **THEN** 系統回傳 HTTP 502 `{"detail": "Failed to fetch activities from Strava"}`

---

### Requirement: 取得單一活動詳情

系統 SHALL 提供 `GET /activities/{id}` 端點，回傳指定活動的完整數據，包含 `distance`、`moving_time`、`elapsed_time`、`average_heartrate`、`max_heartrate`、`average_cadence`、`total_elevation_gain`、`splits_metric`，以及 GPX stream URL（`/activities/{id}/streams?keys=latlng,altitude`）。

#### Scenario: 取得存在的活動詳情

- **WHEN** 用戶呼叫 `GET /activities/{id}`，且該活動屬於此用戶
- **THEN** 系統回傳完整活動數據 JSON，包含 `gpx_stream_url` 欄位

#### Scenario: 存取他人活動

- **WHEN** 用戶嘗試存取不屬於自己的 activity_id
- **THEN** 系統回傳 HTTP 404 `{"detail": "Activity not found"}`

#### Scenario: 活動不存在

- **WHEN** Strava API 回傳 404
- **THEN** 系統回傳 HTTP 404 `{"detail": "Activity not found"}`

---

### Requirement: 取得活動 GPX Stream

系統 SHALL 能從 Strava API 取得活動的 `latlng` 與 `altitude` stream 資料，供前端 Leaflet 地圖渲染使用。GPX stream 資料作為活動詳情的一部分，或透過獨立 stream URL 提供。

#### Scenario: 成功取得 GPX 資料

- **WHEN** 前端請求活動的地圖資料
- **THEN** 系統回傳包含 `lat/lng` 座標陣列與 `altitude` 陣列的資料，前端可直接渲染 Leaflet polyline

#### Scenario: 活動無 GPS 資料

- **WHEN** Strava 活動不包含 GPS 資料（如室內跑步機）
- **THEN** `gpx_stream_url` 欄位為 `null`，前端隱藏地圖元件

---

### Requirement: 用戶活動所有權驗證

系統 SHALL 在所有活動相關端點驗證活動確實屬於當前登入用戶，防止 IDOR（Insecure Direct Object Reference）。

#### Scenario: 跨用戶存取嘗試

- **WHEN** 用戶 A 嘗試用合法 JWT 存取用戶 B 的 activity_id
- **THEN** 系統回傳 HTTP 404（不透露資源存在）
