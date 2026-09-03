// 後端 API 薄封裝。開發時走 Vite proxy(/api → 後端,見 vite.config.js)。

async function req(path, options) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `請求失敗(${res.status})`);
  }
  return res.json();
}

const post = (path, body) =>
  req(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });

export const api = {
  overview: () => req("/overview"),
  getBoard: (projectId) => req(`/projects/${projectId}/board`),
  createProject: (payload) => post("/projects", payload),

  adopt: (suggestionId) => post(`/suggestions/${suggestionId}/adopt`),
  skip: (suggestionId) => post(`/suggestions/${suggestionId}/skip`),
  updateScore: (moduleId, value, speed = "internal") =>
    post(`/modules/${moduleId}/score`, { value, speed }),

  setModel: (moduleId, modelKey) => post(`/modules/${moduleId}/model`, { model_key: modelKey }),
  setTask: (moduleId, task, taskNote) =>
    post(`/modules/${moduleId}/task`, { task, task_note: taskNote }),

  toggleChannel: (moduleId, channel) => post(`/modules/${moduleId}/channels`, { channel }),
  applyAccount: (accountId) => post(`/accounts/${accountId}/apply`),

  reviewOutput: (outputId, decision) => post(`/outputs/${outputId}/review`, { decision }),
};
