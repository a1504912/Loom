// Atelier 專案看板。深色左欄 + 藍圖風格主區 + 橫向流水線。
import { useEffect, useState } from "react";
import { api } from "./api.js";
import Corners from "./components/Corners.jsx";
import ModuleRow from "./components/ModuleRow.jsx";
import { OUT_STATE, STAGE_LABEL } from "./constants.js";

const pad2 = (n) => String(n).padStart(2, "0");

const CAT_LABEL = { money: "記帳工具", internal: "內部工具", client: "客戶委託", other: "其他" };

export default function App() {
  const [overview, setOverview] = useState(null);
  const [board, setBoard] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [cat, setCat] = useState("all");
  const [advanced, setAdvanced] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [view, setView] = useState(null); // 產出審核對話框
  const [confirm, setConfirm] = useState(null); // 高風險採用確認(存整張 card)

  // 初次載入:總覽 + 第一個案子的看板
  useEffect(() => {
    (async () => {
      try {
        const ov = await api.overview();
        setOverview(ov);
        if (ov.projects.length) {
          const id = ov.projects[0].id;
          setSelectedId(id);
          setBoard(await api.getBoard(id));
        }
      } catch (e) {
        setError(e.message);
      }
    })();
  }, []);

  async function applyBoard(nextBoard) {
    setBoard(nextBoard);
    try {
      setOverview(await api.overview());
    } catch (e) {
      setError(e.message);
    }
  }

  async function run(fn) {
    setBusy(true);
    setError("");
    try {
      const b = await fn();
      if (b) await applyBoard(b);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const selectProject = (id) =>
    run(async () => {
      setSelectedId(id);
      return api.getBoard(id);
    });

  const createProject = () =>
    run(async () => {
      const name = "新案子 " + (overview ? overview.projects.length + 1 : 1);
      const b = await api.createProject({
        name,
        type: "accounting_app",
        tags: ["accounting", "payment", "mobile"],
        category: "記帳工具",
        cat_key: "money",
      });
      setSelectedId(b.project_id);
      return b;
    });

  // 採用建議:高風險先確認,否則直接生效
  const adopt = (card) => {
    if (card.needs_confirmation) {
      setConfirm(card);
      return;
    }
    run(() => api.adopt(card.id));
  };
  const doConfirm = () => {
    const card = confirm;
    setConfirm(null);
    run(() => api.adopt(card.id));
  };

  const skip = (id) => run(() => api.skip(id));
  const score = (moduleId, value) => run(() => api.updateScore(moduleId, value));
  const setModel = (moduleId, key) => run(() => api.setModel(moduleId, key));
  const setTask = (moduleId, task, note) => run(() => api.setTask(moduleId, task, note));
  const toggleChannel = (moduleId, channel) => run(() => api.toggleChannel(moduleId, channel));
  const applyAccount = (accountId) => run(() => api.applyAccount(accountId));
  const openOutput = (o, moduleName) => setView({ ...o, moduleName });
  const reviewOutput = (decision) => {
    const id = view.id;
    setView(null);
    run(() => api.reviewOutput(id, decision));
  };

  // 左欄分組
  const projects = overview ? overview.projects : [];
  const visible = projects.filter((p) => cat === "all" || p.cat_key === cat);
  const running = visible.filter((p) => p.stage === "dev");
  const maintaining = visible.filter((p) => p.stage === "maintain");

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "272px 1fr",
        height: "100vh",
        background: "var(--color-bg)",
        color: "var(--color-text)",
        fontFamily: "var(--font-body)",
        overflow: "hidden",
      }}
    >
      {/* ── 左欄 Rail ── */}
      <aside
        style={{
          background: "var(--color-accent-900)",
          color: "var(--color-accent-100)",
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-6)",
          padding: "var(--space-6) var(--space-4)",
          borderRight: "1px solid color-mix(in srgb, var(--color-accent) 40%, transparent)",
          overflowY: "auto",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span
              style={{
                width: "9px",
                height: "9px",
                background: "var(--color-accent)",
                display: "block",
                boxShadow: "0 0 0 3px color-mix(in srgb,var(--color-accent) 25%,transparent)",
              }}
            />
            <span style={{ fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: "20px", letterSpacing: ".16em" }}>
              ATELIER
            </span>
          </div>
          <div style={{ fontSize: "11px", letterSpacing: ".14em", textTransform: "uppercase", color: "var(--color-accent-300)" }}>
            多流程專案系統
          </div>
        </div>

        <button className="btn btn-primary btn-block" style={{ marginTop: 0 }} disabled={busy} onClick={createProject}>
          ＋ 開新案子
        </button>

        {/* 分類 */}
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
          <h6 style={{ margin: 0, color: "var(--color-accent-200)" }}>分類</h6>
          <div style={{ display: "flex", flexDirection: "column", gap: "1px" }}>
            {(overview ? overview.categories : []).map((c) => {
              const on = c.key === cat;
              return (
                <button
                  key={c.key}
                  onClick={() => setCat(c.key)}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "6px 10px",
                    border: "1px solid " + (on ? "var(--color-accent)" : "transparent"),
                    background: on ? "var(--color-accent)" : "transparent",
                    cursor: "pointer",
                    fontSize: "14px",
                    textAlign: "left",
                    color: on ? "var(--color-bg)" : "var(--color-accent-100)",
                    fontFamily: "var(--font-body)",
                  }}
                >
                  <span>{c.name}</span>
                  <span
                    style={{
                      fontSize: "11px",
                      fontVariantNumeric: "tabular-nums",
                      color: on ? "var(--color-accent-900)" : "var(--color-accent-300)",
                    }}
                  >
                    {c.count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        <RailGroup
          title="執行中 · 開發階段"
          filled
          count={running.length}
          projects={running}
          selectedId={selectedId}
          onSelect={selectProject}
          emptyText="這個分類沒有執行中的案子。"
        />
        <RailGroup
          title="維護中 · 優化階段"
          filled={false}
          count={maintaining.length}
          projects={maintaining}
          selectedId={selectedId}
          onSelect={selectProject}
          emptyText="這個分類沒有維護中的案子。"
        />
      </aside>

      {/* ── 主區 ── */}
      <main
        style={{
          overflowY: "auto",
          backgroundImage:
            "repeating-linear-gradient(to right,color-mix(in srgb,var(--color-accent) 8%,transparent) 0 1px,transparent 1px 68px),repeating-linear-gradient(to bottom,color-mix(in srgb,var(--color-accent) 8%,transparent) 0 1px,transparent 1px 68px)",
        }}
      >
        {error && (
          <div style={{ padding: "var(--space-3) var(--space-8)", background: "var(--color-accent-100)", color: "var(--color-accent-800)", fontSize: "13px" }}>
            {error}
          </div>
        )}

        {board ? (
          <>
            {/* 標頭 */}
            <div style={{ display: "flex", alignItems: "flex-start", gap: "var(--space-6)", padding: "var(--space-6) var(--space-8)", borderBottom: "1px solid var(--color-divider)" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)", flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)", fontSize: "11px", letterSpacing: ".14em", textTransform: "uppercase", color: "var(--color-neutral-600)" }}>
                  <span>{board.category}</span>
                  <span>／</span>
                  <span>{board.project_type}</span>
                </div>
                <h2 style={{ margin: 0 }}>{board.project_name}</h2>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  {board.tags.map((t) => (
                    <span key={t} className="tag tag-outline">
                      {t}
                    </span>
                  ))}
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "var(--space-3)" }}>
                <label className="radio" style={{ gap: "8px", fontSize: "13px", whiteSpace: "nowrap", color: "var(--color-neutral-700)" }}>
                  <input type="checkbox" checked={advanced} onChange={(e) => setAdvanced(e.target.checked)} />
                  <span
                    className="dot"
                    style={
                      advanced
                        ? { borderColor: "var(--color-accent)", background: "var(--color-accent)", boxShadow: "inset 0 0 0 4px var(--color-bg)", borderRadius: 0 }
                        : { borderRadius: 0 }
                    }
                  />
                  進階(工作台)
                </label>
                <div className="blueprint" style={{ display: "flex", alignItems: "flex-end", gap: "var(--space-4)", padding: "var(--space-3) var(--space-4)" }}>
                  <Corners />
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <div style={{ fontSize: "11px", letterSpacing: ".14em", textTransform: "uppercase", color: "var(--color-neutral-600)" }}>整體健康度</div>
                    <div style={{ fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: "34px", lineHeight: 1, letterSpacing: ".04em", fontVariantNumeric: "tabular-nums" }}>
                      {board.health}
                    </div>
                  </div>
                  <TrendBars trend={board.trend} />
                  <div style={{ fontSize: "10px", color: "var(--color-neutral-600)", paddingBottom: "2px" }}>近 6 週</div>
                </div>
              </div>
            </div>

            {/* HUD 讀數條 */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "var(--space-8)",
                padding: "var(--space-3) var(--space-8)",
                whiteSpace: "nowrap",
                overflowX: "auto",
                borderBottom: "1px solid var(--color-divider)",
                background: "color-mix(in srgb,var(--color-accent) 7%,transparent)",
                fontSize: "11px",
                letterSpacing: ".14em",
                textTransform: "uppercase",
                color: "var(--color-neutral-600)",
              }}
            >
              {overview &&
                [
                  { label: "案子", value: pad2(overview.hud.project_count) },
                  { label: "平均健康度", value: overview.hud.avg_health },
                  { label: "待決定", value: pad2(overview.hud.pending) },
                  { label: "門檻模式", value: advanced ? "工作台" : "看板" },
                ].map((r) => (
                  <span key={r.label} style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
                    <span>{r.label}</span>
                    <span style={{ fontFamily: "var(--font-heading)", fontSize: "15px", letterSpacing: ".04em", fontVariantNumeric: "tabular-nums", color: "var(--color-text)" }}>
                      {r.value}
                    </span>
                  </span>
                ))}
              <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ width: "6px", height: "6px", background: "var(--color-accent)", display: "block" }} />
                <span>系統運轉中</span>
              </span>
            </div>

            {/* 流水線 */}
            <div style={{ padding: "var(--space-8)", display: "flex", flexDirection: "column", gap: "var(--space-6)" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: "var(--space-3)" }}>
                <h4 style={{ margin: 0 }}>流水線</h4>
                <span style={{ fontSize: "12px", color: "var(--color-neutral-600)" }}>
                  四個分工線性往前;掉到門檻下由系統提建議,你拍板。
                </span>
              </div>
              <div style={{ display: "grid", gridAutoFlow: "column", gridAutoColumns: "394px", gap: "var(--space-6)", alignItems: "start", overflowX: "auto", paddingBottom: "var(--space-4)" }}>
                {board.modules.map((m, i) => (
                  <ModuleRow
                    key={m.id}
                    module={m}
                    index={i}
                    total={board.modules.length}
                    advanced={advanced}
                    busy={busy}
                    onAdopt={adopt}
                    onSkip={skip}
                    onScore={score}
                    onSetModel={setModel}
                    onSetTask={setTask}
                    onToggleChannel={toggleChannel}
                    onApplyAccount={applyAccount}
                    onOpenOutput={openOutput}
                  />
                ))}
              </div>
            </div>
          </>
        ) : (
          <div style={{ padding: "var(--space-8)", color: "var(--color-neutral-600)" }}>載入中…</div>
        )}
      </main>

      {/* 產出審核對話框 */}
      {view && (
        <OutputDialog view={view} onClose={() => setView(null)} onReview={reviewOutput} busy={busy} />
      )}

      {/* 高風險採用確認 */}
      {confirm && (
        <ConfirmDialog card={confirm} onCancel={() => setConfirm(null)} onConfirm={doConfirm} busy={busy} />
      )}
    </div>
  );
}

// ── 左欄分組 ──
function RailGroup({ title, filled, count, projects, selectedId, onSelect, emptyText }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <span
          style={{
            width: "7px",
            height: "7px",
            display: "block",
            background: filled ? "var(--color-accent)" : "transparent",
            border: filled ? "none" : "1px solid var(--color-accent)",
          }}
        />
        <h6 style={{ margin: 0, whiteSpace: "nowrap" }}>{title}</h6>
        <span style={{ marginLeft: "auto", fontSize: "11px", color: "var(--color-accent-300)" }}>{count}</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
        {projects.map((p) => {
          const on = p.id === selectedId;
          return (
            <button
              key={p.id}
              onClick={() => onSelect(p.id)}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "4px",
                width: "100%",
                padding: "9px 11px",
                cursor: "pointer",
                textAlign: "left",
                fontFamily: "var(--font-body)",
                color: "var(--color-accent-100)",
                border: "1px solid " + (on ? "var(--color-accent)" : "color-mix(in srgb, var(--color-accent) 32%, transparent)"),
                background: on ? "color-mix(in srgb, var(--color-accent) 22%, transparent)" : "transparent",
              }}
            >
              <span style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: "8px" }}>
                <span style={{ fontFamily: "var(--font-heading)", fontWeight: 600, fontSize: "15px" }}>{p.name}</span>
                <span
                  style={{
                    fontFamily: "var(--font-heading)",
                    fontWeight: 600,
                    fontSize: "15px",
                    fontVariantNumeric: "tabular-nums",
                    color: p.health < 70 ? "var(--color-accent-100)" : "var(--color-accent-400)",
                  }}
                >
                  {p.health}
                </span>
              </span>
              <span style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", color: "var(--color-accent-300)" }}>
                <span style={{ whiteSpace: "nowrap" }}>{CAT_LABEL[p.cat_key] || p.category}</span>
                <span>·</span>
                <span style={{ whiteSpace: "nowrap" }}>{STAGE_LABEL[p.stage]}</span>
              </span>
              {p.alerts > 0 && (
                <span className="tag tag-accent" style={{ alignSelf: "flex-start" }}>
                  {p.alerts} 張建議待決定
                </span>
              )}
            </button>
          );
        })}
        {projects.length === 0 && (
          <p style={{ margin: 0, fontSize: "12px", color: "var(--color-accent-300)" }}>{emptyText}</p>
        )}
      </div>
    </div>
  );
}

// ── 健康度趨勢柱 ──
function TrendBars({ trend }) {
  const list = trend && trend.length ? trend : [0, 0, 0, 0, 0, 0];
  const maxT = Math.max(...list, 100);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: "3px", height: "38px" }}>
      {list.map((v, i) => (
        <span
          key={i}
          style={{
            display: "block",
            width: "7px",
            height: Math.round((v / maxT) * 38) + "px",
            background: i === list.length - 1 ? "var(--color-accent)" : "var(--color-neutral-300)",
          }}
        />
      ))}
    </div>
  );
}

// ── 產出審核對話框 ──
function OutputDialog({ view, onClose, onReview, busy }) {
  const pending = view.state === "review";
  const stateStyle = {
    fontSize: "11px",
    letterSpacing: "0.08em",
    padding: "2px 8px",
    background: view.state === "review" ? "var(--color-accent-100)" : view.state === "rejected" ? "var(--color-neutral-200)" : "transparent",
    border: "1px solid " + (view.state === "review" ? "var(--color-accent)" : "var(--color-divider)"),
    color: view.state === "review" ? "var(--color-accent-800)" : view.state === "rejected" ? "var(--color-neutral-800)" : "var(--color-neutral-600)",
  };
  return (
    <div className="dialog-backdrop">
      <div className="dialog blueprint" style={{ background: "var(--color-bg)", width: "min(620px, 100%)" }}>
        <Corners />
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-2)" }}>
          <span style={stateStyle}>{OUT_STATE[view.state]}</span>
          <span style={{ fontSize: "11px", color: "var(--color-neutral-600)" }}>
            {view.moduleName} · {view.by} · {view.when}
          </span>
        </div>
        <div className="dialog-title">{view.title}</div>
        <div className="dialog-body" style={{ display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {view.items.map((t, i) => (
              <div key={i} style={{ display: "flex", gap: "10px", fontSize: "13px", lineHeight: 1.65 }}>
                <span style={{ color: "var(--color-neutral-500)", fontVariantNumeric: "tabular-nums" }}>{pad2(i + 1)}</span>
                <span>{t}</span>
              </div>
            ))}
          </div>
          {pending && (
            <p style={{ margin: 0, fontSize: "12px", color: "var(--color-accent-700)" }}>
              核可後這一層會計入健康度;退回會把任務留在原地並附上你的說明。
            </p>
          )}
        </div>
        <div className="dialog-actions">
          <button className="btn btn-ghost" onClick={onClose}>關閉</button>
          {pending && (
            <>
              <button className="btn btn-secondary" disabled={busy} onClick={() => onReview("reject")}>退回重做</button>
              <button className="btn btn-primary" disabled={busy} onClick={() => onReview("approve")}>核可</button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ── 高風險採用確認 ──
function ConfirmDialog({ card, onCancel, onConfirm, busy }) {
  return (
    <div className="dialog-backdrop">
      <div className="dialog blueprint" style={{ background: "var(--color-bg)", width: "min(480px, 100%)" }}>
        <Corners />
        <div className="tag tag-accent" style={{ alignSelf: "flex-start" }}>高風險 · 需要你確認</div>
        <div className="dialog-title">採用「{card.skill_name}」?</div>
        <div className="dialog-body" style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}>
          <p style={{ margin: 0 }}>{card.why}</p>
          <p style={{ margin: 0 }}>{card.predicted_effect}</p>
          {card.conflict_group && (
            <p style={{ margin: 0, color: "var(--color-accent-700)" }}>採用後,同組的另一個建議會自動略過。</p>
          )}
        </div>
        <div className="dialog-actions">
          <button className="btn btn-secondary" disabled={busy} onClick={onCancel}>取消</button>
          <button className="btn btn-primary" disabled={busy} onClick={onConfirm}>確認採用</button>
        </div>
      </div>
    </div>
  );
}
