// 看板卡片 — 必備三件事:為什麼、預期效果、衝突標記。
// 一眼決定:採用 / 先略過。高風險強制人工確認。

export default function SuggestionCard({ card, onAdopt, onSkip, busy }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center gap-2">
        <span className="font-medium text-slate-900">{card.skill_name}</span>
        {card.conflict_group && (
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-700">
            二選一
          </span>
        )}
        {card.needs_confirmation && (
          <span className="rounded-full bg-rose-100 px-2 py-0.5 text-xs text-rose-700">
            需要你確認
          </span>
        )}
      </div>

      <p className="mb-1 text-sm text-slate-600">
        <span className="font-medium text-slate-500">為什麼:</span>
        {card.why}
      </p>
      {card.predicted_effect && (
        <p className="mb-3 text-sm text-slate-600">
          <span className="font-medium text-slate-500">預期效果:</span>
          {card.predicted_effect}
        </p>
      )}

      <div className="flex gap-2">
        <button
          disabled={busy}
          onClick={() => onAdopt(card.id)}
          className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          採用
        </button>
        <button
          disabled={busy}
          onClick={() => onSkip(card.id)}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 disabled:opacity-50"
        >
          先略過
        </button>
      </div>
    </div>
  );
}
