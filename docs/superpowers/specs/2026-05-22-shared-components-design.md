# Shared Component Design — Running Analytics AI

**Date:** 2026-05-22
**Scope:** Frontend shared components for ActivitiesPage and ActivityDetailPage
**Reference:** Figma file `aXWF4fYRx5vUg1JIEyPlNx` (pages: Activities Page node `3:2`, Activity Detail Page node `3:3`)

---

## 1. Background

The Figma design has three pages: Login Page, Activities Page, and Activity Detail Page. Activities Page and Activity Detail Page share structural patterns across the Header, metric displays, and AI chat panel. This document defines the six shared components extracted from those patterns to ensure consistent implementation and maximum reuse.

---

## 2. Component Inventory

| Component | File | Used In |
|-----------|------|---------|
| `AppHeader` | `src/components/AppHeader.tsx` | ActivitiesPage, ActivityDetailPage |
| `MetricItem` | `src/components/MetricItem.tsx` | ActivityCard (Metrics Row) |
| `MetricCard` | `src/components/MetricCard.tsx` | ActivityDetailPage (Metrics Grid) |
| `ActivityTag` | `src/components/ActivityTag.tsx` | ActivityCard |
| `ChatMessage` | `src/components/ChatMessage.tsx` | AiChatPanel |
| `AiChatPanel` | `src/components/AiChatPanel.tsx` | ActivitiesPage, ActivityDetailPage |

**Out of scope (page-specific):**
- `ActivityCard` — ActivitiesPage only; composes MetricItem + ActivityTag
- `ActivityMap` — ActivityDetailPage only; Leaflet + leaflet-gpx
- `SplitRow` — ActivityDetailPage only; per-km pace bar

---

## 3. Props Interfaces

### AppHeader

```typescript
interface AppHeaderProps {
  user: { name: string; avatarUrl: string }
}
```

Full-width (1440px), height 64px. Shows logo + "Running Analytics AI" on the left, user avatar + name on the right. Corresponds to Figma symbol `Navbar/App Header` (node `26:2`).

---

### MetricItem

```typescript
interface MetricItemProps {
  label: string   // e.g. "距離" | "配速" | "時間" | "心率" | "爬升"
  value: string   // e.g. "8.42 km" | "5'23\"/km" | "45:22"
}
```

Small metric display used inside `ActivityCard`'s Metrics Row. Value and unit are combined into a single string because the Activity Card layout does not require separate styling for the unit. No icon.

Layout: label (13px, `#8b97a8`) stacked above value (18px, white, medium weight).

---

### MetricCard

```typescript
interface MetricCardProps {
  icon: string          // emoji: "📏" | "⚡" | "⏱" | "❤️" | "⛰" | "🔥"
  label: string         // "距離" | "配速" | "時間" | "心率" | "爬升" | "熱量"
  value: string         // numeric part only: "8.42" | "5'23\"" | "45:22" | "152" | "+68" | "521"
  unit?: string         // "km" | "/km" | "bpm" | "m" | "kcal" (omit for 時間)
  valueColor?: string   // see exact color mapping below
}
```

Large metric card used in ActivityDetailPage's 6-column Metrics Grid. Value and unit are separate props because the Detail Grid renders them at different sizes (value 22px bold, unit 12px `#8b97a8`).

Layout: icon + label row (12px, `#8b97a8`) above value + unit row. Card background `#151a22`, border `#1e2630`, border-radius `10px`, padding `14px`, height 76px.

**Exact color mapping per metric (from Figma):**

| Metric | valueColor |
|--------|-----------|
| 距離 | `#f97316` (orange) |
| 配速 | `#22c55e` (green) |
| 時間 | `#5e98f8` (blue) |
| 心率 | `#ef4444` (red) |
| 爬升 | `#d0ab18` (gold) |
| 熱量 | `#f97316` (orange) |

---

### ActivityTag

```typescript
interface ActivityTagProps {
  label: string
}
```

Pill-shaped label badge shown in the top-right corner of `ActivityCard`. All tag types share a single visual style — background `rgba(249,115,22,0.15)` (semi-transparent orange), text `#f97316`, 12px medium weight, border-radius `4px`, padding `4px 10px`. No variant prop needed.

---

### ChatMessage

```typescript
interface ChatMessageProps {
  role: 'ai' | 'user'
  content: string
  isStreaming?: boolean  // appends ▌ cursor at end of content when true
}
```

Single conversation message. Used exclusively inside `AiChatPanel`.

**AI message** (`role="ai"`): background `#151a22`, shows "AI 教練" label (15px, `#8b97a8`) above content (14px, white), padding 14px, border-radius 8px.

**User message** (`role="user"`): background `#1e2630`, content only (17px, white), padding `12px 14px`, border-radius 8px.

**Streaming state** (`isStreaming=true`): appends `▌` to content. The cursor is rendered as a `<span>` with a CSS blink animation so it can be toggled independently of content updates.

---

### AiChatPanel

```typescript
interface AiChatPanelProps {
  scope: 'list' | 'activity'
  activityId?: string  // required when scope='activity'
}
```

Full right-side AI chat panel. Width is determined by the parent page layout (400px on ActivitiesPage, 380px on ActivityDetailPage) — the component takes `width: 100%` and does not hard-code a width.

Internal structure:
- **ChatHeader**: green dot + "AI 跑步教練" title (18px, white)
- **ChatMessages**: scrollable list of `ChatMessage` components
- **ChatInputBar**: text input + orange send button (`#f97316`)

Default placeholder text per scope:
- `scope="list"` → `"分析我近一個月的跑步活動"`
- `scope="activity"` → `"分析這次跑步活動"`

Conversation data is loaded via `useConversation(scope, activityId)` hook internally — the component does not accept messages as a prop.

---

## 4. Page Integration

### ActivitiesPage layout

```
AppHeader
Body (flex row, full height below header)
├── Left Column (flex: 1, ~1040px)
│   ├── Heading Row ("我的跑步活動" + Sync Badge)
│   └── ActivityCard[] (page-specific)
│       ├── MetricItem × 5
│       └── ActivityTag
└── AiChatPanel scope="list" (w-[400px], shrink-0)
```

### ActivityDetailPage layout

```
AppHeader
Body (flex row, full height below header)
├── Main Content (flex: 1, ~1060px)
│   ├── Title Row (Back button + activity title)
│   ├── ActivityMap (page-specific, h-[230px])
│   ├── Metrics Grid (grid grid-cols-6, h-[76px])
│   │   └── MetricCard × 6
│   └── Splits Table (page-specific)
│       └── SplitRow × N
└── AiChatPanel scope="activity" activityId={id} (w-[380px], shrink-0)
```

---

## 5. Design Tokens

Extracted from Figma. Map to Tailwind config or CSS variables.

```typescript
// tailwind.config.ts — extend colors
colors: {
  'bg-base':        '#0b0e13',   // page background
  'bg-surface':     '#151a22',   // card / panel background
  'bg-elevated':    '#1e2630',   // border, divider, user message bg
  'accent':         '#f97316',   // primary CTA, tag text, 距離/熱量 metric
  'text-primary':   '#ffffff',
  'text-secondary': '#8b97a8',
  'text-muted':     '#636f80',
  // MetricCard value colors (from Figma)
  'metric-distance':'#f97316',   // 距離 orange
  'metric-pace':    '#22c55e',   // 配速 green
  'metric-time':    '#5e98f8',   // 時間 blue
  'metric-hr':      '#ef4444',   // 心率 red
  'metric-elev':    '#d0ab18',   // 爬升 gold
  'metric-cal':     '#f97316',   // 熱量 orange (same as accent)
  // ActivityTag
  'tag-bg':         'rgba(249,115,22,0.15)',
}
```

---

## 6. Testing Plan

| Component | Test focus |
|-----------|-----------|
| `MetricItem` | Renders label + value correctly |
| `MetricCard` | Applies valueColor; omits unit element when prop absent |
| `ActivityTag` | Renders correct background color per variant |
| `ChatMessage` | AI vs user layout; ▌ cursor present when isStreaming=true |
| `AiChatPanel` | Default placeholder per scope; scrolls to bottom on new message |
| `AppHeader` | Renders user name and avatar src |
