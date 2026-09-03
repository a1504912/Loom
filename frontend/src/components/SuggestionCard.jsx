// 建議卡(藍圖卡)。必備三件事:為什麼、預期效果、衝突標記。
import Corners from "./Corners.jsx";

export default function SuggestionCard({ card, onAdopt, onSkip, busy }) {
  return (
    <div
      className="card blueprint"
      style={{ background: "var(--color-bg)", gap: "var(--space-2)", padding: "var(--space-4)" }}
    >
      <Corners />
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
        <span className="card-kicker">建議</span>
        <span style={{ fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: "17px" }}>
          {card.skill_name}
        </span>
        {card.conflict_group && <span className="tag tag-neutral">二選一</span>}
        {card.needs_confirmation && <span className="tag tag-accent">需要你確認</span>}
      </div>
      <p style={{ margin: 0, fontSize: "13px", lineHeight: 1.65 }}>
        <span style={{ color: "var(--color-neutral-600)" }}>為什麼:</span>
        {card.why}
      </p>
      <p style={{ margin: 0, fontSize: "13px", lineHeight: 1.65 }}>
        <span style={{ color: "var(--color-neutral-600)" }}>預期效果:</span>
        {card.predicted_effect}
      </p>
      <div style={{ display: "flex", gap: "var(--space-2)", marginTop: "var(--space-2)" }}>
        <button className="btn btn-primary" disabled={busy} onClick={() => onAdopt(card)}>
          採用
        </button>
        <button className="btn btn-secondary" disabled={busy} onClick={() => onSkip(card.id)}>
          先略過
        </button>
      </div>
    </div>
  );
}
