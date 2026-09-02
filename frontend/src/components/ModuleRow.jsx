// 健康度列。安好的模組只留一行;needs_attention 展開成建議卡。
// 進階(工作台)模式多顯示分數/門檻與一個「更新健康度」的示範控制。

import { useState } from "react";
import SuggestionCard from "./SuggestionCard.jsx";

const STATUS_LABEL = {
  not_started: "尚未開始",
  active: "進行中",
  resting: "待命中",
  needs_attention: "需要注意",
};

const STATUS_DOT = {
  not_started: "bg-slate-300",
  active: "bg-sky-400",
  resting: "bg-emerald-400",
  needs_attention: "bg-rose-400",
};

function healthColor(score) {
  if (score >= 80) return "text-emerald-600";
  if (score >= 60) return "text-amber-600";
  return "text-rose-600";
}

export default function ModuleRow({ module, advanced, onAdopt, onSkip, onScore, busy }) {
  const [draftScore, setDraftScore] = useState(module.score);
  const hasCards = module.open_suggestions.length > 0;
  const attention = module.status === "needs_attention" || hasCards;

  return (
    <div className="rounded-xl border border-slate-200 bg-white">
      {/* 一行摘要 */}
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <span className={`h-2.5 w-2.5 rounded-full ${STATUS_DOT[module.status]}`} />
          <span className="font-medium text-slate-900">{module.name}</span>
          <span className="text-xs text-slate-400">
            {STATUS_LABEL[module.status] || module.status}
          </span>
          {module.mounted_skills.length > 0 && (
            <span className="text-xs text-slate-500">
              已掛:{module.mounted_skills.join("、")}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {module.mounted_skills.length === 0 && !hasCards && (
            <span className="text-xs text-slate-300">—</span>
          )}
          {advanced && (
            <span className={`text-sm font-semibold ${healthColor(module.score)}`}>
              健康度 {module.score}
            </span>
          )}
        </div>
      </div>

      {/* 需要注意 → 展開卡片 */}
      {attention && (
        <div className="space-y-3 border-t border-slate-100 bg-slate-50 px-4 py-3">
          {module.open_suggestions.map((card) => (
            <SuggestionCard
              key={card.id}
              card={card}
              onAdopt={onAdopt}
              onSkip={onSkip}
              busy={busy}
            />
          ))}
          {!hasCards && (
            <p className="text-sm text-slate-500">目前沒有待處理的建議。</p>
          )}
        </div>
      )}

      {/* 工作台層:示範用「更新健康度」控制(對外文案用「健康度」而非 threshold) */}
      {advanced && (
        <div className="flex items-center gap-2 border-t border-slate-100 px-4 py-2 text-xs text-slate-500">
          <span>門檻 {module.threshold}</span>
          <span className="mx-1">·</span>
          <label className="flex items-center gap-1">
            回報健康度
            <input
              type="number"
              min={0}
              max={100}
              value={draftScore}
              onChange={(e) => setDraftScore(Number(e.target.value))}
              className="w-16 rounded border border-slate-300 px-1 py-0.5"
            />
          </label>
          <button
            disabled={busy}
            onClick={() => onScore(module.id, draftScore)}
            className="rounded border border-slate-300 px-2 py-0.5 hover:bg-slate-100 disabled:opacity-50"
          >
            更新
          </button>
        </div>
      )}
    </div>
  );
}
