// Atelier 看板。漸進揭露:對話式開案 → 看板層 → 工作台層(進階)。

import { useEffect, useState } from "react";
import { api } from "./api.js";
import ModuleRow from "./components/ModuleRow.jsx";

// 對話層的「一句話開案」預設方案:自然語言 → type + tags。
const PRESETS = [
  {
    phrase: "我要做記帳 app",
    name: "記帳 app",
    type: "accounting_app",
    tags: ["accounting", "payment", "mobile"],
  },
  {
    phrase: "我要做一般專案",
    name: "新專案",
    type: "generic",
    tags: [],
  },
];

export default function App() {
  const [projects, setProjects] = useState([]);
  const [board, setBoard] = useState(null);
  const [advanced, setAdvanced] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listProjects().then(setProjects).catch((e) => setError(e.message));
  }, []);

  async function run(fn) {
    setBusy(true);
    setError("");
    try {
      const next = await fn();
      if (next) setBoard(next);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  const createFromPreset = (preset) =>
    run(async () => {
      const b = await api.createProject(preset);
      setProjects(await api.listProjects());
      return b;
    });

  const openBoard = (id) => run(() => api.getBoard(id));
  const adopt = (id) => run(() => api.adopt(id));
  const skip = (id) => run(() => api.skip(id));
  const score = (moduleId, value) => run(() => api.updateScore(moduleId, value));

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Atelier</h1>
          <p className="text-sm text-slate-500">
            建案子 → 排好流程 → 掛能力,系統主動建議、由你拍板。
          </p>
        </div>
        <label className="flex items-center gap-2 text-sm text-slate-500">
          <input
            type="checkbox"
            checked={advanced}
            onChange={(e) => setAdvanced(e.target.checked)}
          />
          進階(工作台)
        </label>
      </header>

      {error && (
        <div className="mb-4 rounded-md bg-rose-50 px-4 py-2 text-sm text-rose-700">
          {error}
        </div>
      )}

      {/* 對話層:一句話開案 */}
      {!board && (
        <section className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-5">
            <p className="mb-3 text-slate-700">想做什麼?挑一個,我幫你排好整套。</p>
            <div className="flex flex-wrap gap-2">
              {PRESETS.map((p) => (
                <button
                  key={p.type}
                  disabled={busy}
                  onClick={() => createFromPreset(p)}
                  className="rounded-full border border-slate-300 px-4 py-2 text-sm hover:bg-slate-100 disabled:opacity-50"
                >
                  {p.phrase}
                </button>
              ))}
            </div>
          </div>

          {projects.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-5">
              <p className="mb-3 text-sm font-medium text-slate-500">已有的案子</p>
              <ul className="space-y-2">
                {projects.map((p) => (
                  <li key={p.id}>
                    <button
                      onClick={() => openBoard(p.id)}
                      className="text-sm text-sky-700 hover:underline"
                    >
                      {p.name} · {p.type}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {/* 看板層 */}
      {board && (
        <section>
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">
                {board.project_name}
              </h2>
              <p className="text-xs text-slate-400">
                {board.project_type} · {board.project_status} ·{" "}
                {board.tags.join("、")}
              </p>
            </div>
            <button
              onClick={() => setBoard(null)}
              className="text-sm text-slate-500 hover:underline"
            >
              ← 回開案
            </button>
          </div>

          <div className="space-y-3">
            {board.modules.map((m) => (
              <ModuleRow
                key={m.id}
                module={m}
                advanced={advanced}
                onAdopt={adopt}
                onSkip={skip}
                onScore={score}
                busy={busy}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
