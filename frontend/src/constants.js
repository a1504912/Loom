// 靜態顯示對照表 — 對齊設計交接包。這些是固定 UI 文字,不進後端。

export const STATUS = {
  not_started: "尚未開始",
  active: "進行中",
  resting: "待命中",
  needs_attention: "需要注意",
};

export const OUT_STATE = {
  done: "已完成",
  review: "待你確認",
  running: "產出中",
  rejected: "已退回",
};

export const ACC_STATE = { none: "未辦理", applying: "辦理中", ready: "已開通" };

export const MODELS = [
  { key: "claude", label: "Claude", note: "擅長長脈絡與程式重構" },
  { key: "gpt", label: "GPT", note: "擅長泛用推理與整合" },
  { key: "gemini", label: "Gemini", note: "擅長多模態與圖文" },
];

export const DEFAULT_MODEL = {
  design: "gemini",
  code: "claude",
  security: "claude",
  growth: "gpt",
};

export const TASKS = {
  design: ["版面草稿", "元件規格", "流程圖", "文案潤稿"],
  code: ["功能開發", "重構", "測試補齊", "串接外部服務"],
  security: ["風險盤點", "加密設計", "權限檢查", "個資合規"],
  growth: ["成效追蹤設定", "文案產出", "受眾研究", "上架素材"],
};

export const CHANNELS = ["Instagram", "Threads", "Facebook", "LINE 官方帳號", "X", "YouTube"];

export const STAGE_LABEL = { dev: "開發階段", maintain: "優化階段" };

// score 相對 threshold 的色調(對應原型 toneFor)
export function toneFor(score, threshold) {
  if (score < threshold) return "var(--color-accent-800)";
  if (score < threshold + 8) return "var(--color-accent-600)";
  return "var(--color-neutral-600)";
}
