// 流水線的一欄(一個模組 / 分工層)。橫向排列,每層一欄。
import { useState } from "react";
import Corners from "./Corners.jsx";
import SuggestionCard from "./SuggestionCard.jsx";
import {
  ACC_STATE,
  CHANNELS,
  DEFAULT_MODEL,
  MODELS,
  OUT_STATE,
  STATUS,
  TASKS,
  toneFor,
} from "../constants.js";

const KICKER = {
  fontSize: "11px",
  letterSpacing: ".14em",
  textTransform: "uppercase",
  color: "var(--color-neutral-600)",
};

function accountStateStyle(state) {
  return {
    fontSize: "11px",
    letterSpacing: "0.08em",
    padding: "2px 8px",
    whiteSpace: "nowrap",
    background: state === "ready" ? "var(--color-accent-100)" : "transparent",
    border: "1px solid " + (state === "applying" ? "var(--color-accent)" : "var(--color-divider)"),
    color:
      state === "ready" || state === "applying"
        ? "var(--color-accent-800)"
        : "var(--color-neutral-600)",
  };
}

function outputStateStyle(state) {
  return {
    fontSize: "11px",
    letterSpacing: "0.08em",
    padding: "2px 8px",
    whiteSpace: "nowrap",
    background:
      state === "review"
        ? "var(--color-accent-100)"
        : state === "rejected"
        ? "var(--color-neutral-200)"
        : "transparent",
    border: "1px solid " + (state === "review" ? "var(--color-accent)" : "var(--color-divider)"),
    color:
      state === "review"
        ? "var(--color-accent-800)"
        : state === "rejected"
        ? "var(--color-neutral-800)"
        : "var(--color-neutral-600)",
  };
}

export default function ModuleRow({
  module: m,
  index,
  total,
  advanced,
  busy,
  onAdopt,
  onSkip,
  onScore,
  onSetModel,
  onSetTask,
  onToggleChannel,
  onApplyAccount,
  onOpenOutput,
}) {
  const tone = toneFor(m.score, m.threshold);
  const attention = m.status === "needs_attention" || m.open_suggestions.length > 0;
  const picked = m.model_key || DEFAULT_MODEL[m.role_key] || "claude";
  const taskOptions = TASKS[m.role_key] || TASKS.code;
  const modelNote = (MODELS.find((mo) => mo.key === picked) || MODELS[0]).note;
  const pickedChannels = m.accounts.map((a) => a.channel);

  const [note, setNote] = useState(m.task_note || "");
  const [draft, setDraft] = useState(m.score);

  const step = String(index + 1).padStart(2, "0");
  const totalStr = String(total).padStart(2, "0");

  return (
    <div
      className="blueprint"
      style={{
        background: "transparent",
        borderColor: attention ? "var(--color-accent)" : "var(--color-divider)",
      }}
    >
      <Corners />
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-4)",
          padding: "var(--space-4)",
          width: "100%",
          minHeight: "498px",
        }}
      >
        {/* a. 步驟標 */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "var(--space-2)",
            fontFamily: "var(--font-heading)",
            fontWeight: 600,
            fontSize: "13px",
            letterSpacing: ".1em",
            color: "var(--color-neutral-500)",
          }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ width: "14px", height: "1px", background: "var(--color-accent)", display: "block" }} />
            <span>{step}</span>
            <span>/ {totalStr}</span>
          </span>
          <span>{index === total - 1 ? "" : "→"}</span>
        </div>

        {/* b. 名稱 + 狀態 */}
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", flexWrap: "wrap" }}>
          <span style={{ fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: "20px" }}>
            {m.name}
          </span>
          <span
            style={{
              fontSize: "11px",
              letterSpacing: "0.08em",
              padding: "3px 9px",
              background: attention ? "var(--color-accent)" : "var(--color-neutral-100)",
              color: attention ? "var(--color-bg)" : "var(--color-neutral-700)",
            }}
          >
            {STATUS[m.status]}
          </span>
        </div>

        {/* c. 分數 + 進度條 */}
        <div style={{ display: "flex", alignItems: "flex-end", gap: "var(--space-3)" }}>
          <div
            style={{
              fontFamily: "var(--font-heading)",
              fontWeight: 600,
              fontSize: "26px",
              lineHeight: 1,
              fontVariantNumeric: "tabular-nums",
              letterSpacing: "0.04em",
              color: tone,
              minWidth: "44px",
              textAlign: "right",
            }}
          >
            {m.score}
          </div>
          <div style={{ flex: 1, height: "6px", background: "var(--color-neutral-300)", marginBottom: "6px" }}>
            <div style={{ width: m.score + "%", height: "100%", background: tone }} />
          </div>
        </div>

        {/* d. 已掛能力 */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            flexWrap: "wrap",
            fontSize: "12px",
            color: "var(--color-neutral-700)",
          }}
        >
          <span style={{ whiteSpace: "nowrap" }}>
            {m.mounted_skills.length ? "已掛能力" : "尚未掛上能力"}
          </span>
          {m.mounted_skills.map((s) => (
            <span key={s} className="tag tag-neutral" style={{ whiteSpace: "nowrap" }}>
              {s}
            </span>
          ))}
        </div>

        {/* e. 社群通路(僅推廣層) */}
        {m.role_key === "growth" && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "var(--space-2)",
              paddingTop: "var(--space-3)",
              borderTop: "1px solid var(--color-divider)",
            }}
          >
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: "8px" }}>
              <div style={KICKER}>社群通路</div>
              <div style={{ fontSize: "11px", color: "var(--color-neutral-500)" }}>
                {pickedChannels.length ? "已選 " + pickedChannels.length + " 個" : ""}
              </div>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "4px" }}>
              {CHANNELS.map((c) => {
                const on = pickedChannels.includes(c);
                return (
                  <button
                    key={c}
                    className="tag"
                    disabled={busy}
                    onClick={() => onToggleChannel(m.id, c)}
                    style={{
                      cursor: "pointer",
                      fontFamily: "var(--font-body)",
                      border: "1px solid " + (on ? "var(--color-accent)" : "var(--color-divider)"),
                      background: on ? "var(--color-accent)" : "transparent",
                      color: on ? "var(--color-bg)" : "var(--color-neutral-700)",
                      fontWeight: on ? 600 : 400,
                    }}
                  >
                    {c}
                  </button>
                );
              })}
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "1px" }}>
              {m.accounts.map((a) => (
                <div
                  key={a.id}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "6px 9px",
                    border: "1px solid var(--color-divider)",
                    background: "var(--color-bg)",
                  }}
                >
                  <span style={{ fontSize: "13px", fontWeight: 600 }}>{a.channel}</span>
                  <span style={accountStateStyle(a.state)}>{ACC_STATE[a.state]}</span>
                  <span style={{ marginLeft: "auto", fontSize: "11px", color: "var(--color-neutral-600)" }}>
                    {a.handle}
                  </span>
                  {a.state === "none" && (
                    <button
                      className="btn btn-secondary"
                      style={{ padding: "2px 8px", fontSize: "11px" }}
                      disabled={busy}
                      onClick={() => onApplyAccount(a.id)}
                    >
                      辦理帳號
                    </button>
                  )}
                </div>
              ))}
              {pickedChannels.length === 0 && (
                <p style={{ margin: 0, fontSize: "12px", color: "var(--color-neutral-600)" }}>
                  先選要經營的社群,再逐一辦理帳號。
                </p>
              )}
            </div>
          </div>
        )}

        {/* f. 執行模型 */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-2)",
            paddingTop: "var(--space-3)",
            borderTop: "1px solid var(--color-divider)",
          }}
        >
          <div style={KICKER}>執行模型</div>
          <div className="seg" style={{ display: "flex", width: "100%" }}>
            {MODELS.map((mo) => (
              <label
                key={mo.key}
                className="seg-opt"
                style={{ flex: 1, justifyContent: "center", fontSize: "12px", padding: "6px 8px" }}
              >
                <input
                  type="radio"
                  name={`model-${m.id}`}
                  checked={mo.key === picked}
                  disabled={busy}
                  onChange={() => onSetModel(m.id, mo.key)}
                />
                {mo.label}
              </label>
            ))}
          </div>
          <div style={{ fontSize: "11px", color: "var(--color-neutral-600)" }}>{modelNote}</div>
        </div>

        {/* g. 主要任務 */}
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
          <div style={KICKER}>主要任務</div>
          <span style={{ position: "relative", display: "block" }}>
            <select
              className="input"
              style={{
                minHeight: "32px",
                fontSize: "13px",
                width: "100%",
                appearance: "none",
                WebkitAppearance: "none",
                paddingRight: "26px",
              }}
              value={m.task || taskOptions[0]}
              disabled={busy}
              onChange={(e) => onSetTask(m.id, e.target.value, note)}
            >
              {taskOptions.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <span
              style={{
                position: "absolute",
                right: "9px",
                top: "50%",
                transform: "translateY(-50%)",
                pointerEvents: "none",
                fontSize: "10px",
                color: "var(--color-accent)",
              }}
            >
              ▼
            </span>
          </span>
          <input
            className="input"
            style={{ minHeight: "32px", fontSize: "13px" }}
            placeholder="補一句這輪要做什麼"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            onBlur={() => note !== (m.task_note || "") && onSetTask(m.id, m.task || taskOptions[0], note)}
          />
        </div>

        {/* h. 完成結果 */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-2)",
            paddingTop: "var(--space-3)",
            borderTop: "1px solid var(--color-divider)",
          }}
        >
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: "8px" }}>
            <div style={KICKER}>完成結果</div>
            <div style={{ fontSize: "11px", color: "var(--color-neutral-500)" }}>
              {m.outputs.length ? m.outputs.length + " 項" : ""}
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "1px" }}>
            {m.outputs.map((o) => (
              <button
                key={o.id}
                onClick={() => onOpenOutput(o, m.name)}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "2px",
                  width: "100%",
                  textAlign: "left",
                  padding: "7px 9px",
                  cursor: "pointer",
                  fontFamily: "var(--font-body)",
                  color: "var(--color-text)",
                  border: "1px solid " + (o.state === "review" ? "var(--color-accent)" : "var(--color-divider)"),
                  background: "var(--color-bg)",
                }}
              >
                <span style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "8px" }}>
                  <span style={{ fontSize: "13px", fontWeight: 600 }}>{o.title}</span>
                  <span style={outputStateStyle(o.state)}>{OUT_STATE[o.state]}</span>
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", color: "var(--color-neutral-600)" }}>
                  <span>{o.by}</span>
                  <span>·</span>
                  <span>{o.when}</span>
                  <span style={{ marginLeft: "auto" }}>{o.state === "review" ? "點開審核 →" : "點開查看 →"}</span>
                </span>
              </button>
            ))}
            {m.outputs.length === 0 && (
              <p style={{ margin: 0, fontSize: "12px", color: "var(--color-neutral-600)" }}>
                這一層還沒有產出。跑完一輪任務後結果會列在這裡。
              </p>
            )}
          </div>
        </div>
      </div>

      {/* i. 建議卡區(需要注意時展開) */}
      {attention && (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "var(--space-3)",
            padding: "var(--space-4)",
            borderTop: "1px solid var(--color-divider)",
            background: "var(--color-accent-100)",
          }}
        >
          {m.open_suggestions.map((card) => (
            <SuggestionCard key={card.id} card={card} onAdopt={onAdopt} onSkip={onSkip} busy={busy} />
          ))}
          {m.open_suggestions.length === 0 && (
            <p style={{ margin: 0, fontSize: "13px", color: "var(--color-neutral-600)" }}>
              目前沒有待處理的建議。
            </p>
          )}
        </div>
      )}

      {/* j. 進階列 */}
      {advanced && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "var(--space-3)",
            padding: "var(--space-2) var(--space-4)",
            borderTop: "1px solid var(--color-divider)",
            fontSize: "12px",
            color: "var(--color-neutral-700)",
          }}
        >
          <span>門檻 {m.threshold}</span>
          <span>·</span>
          <span>回報健康度</span>
          <input
            className="input"
            type="number"
            style={{ width: "70px", minHeight: "28px", padding: "2px 8px" }}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
          />
          <button
            className="btn btn-secondary"
            style={{ padding: "3px 10px", fontSize: "12px" }}
            disabled={busy}
            onClick={() => onScore(m.id, Number(draft))}
          >
            更新
          </button>
          <span style={{ marginLeft: "auto" }}>{m.role_key}</span>
        </div>
      )}
    </div>
  );
}
