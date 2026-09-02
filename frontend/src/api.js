// 後端 API 薄封裝。開發時走 Vite proxy(/api → :8000)。

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

export const api = {
  listProjects: () => req("/projects"),
  createProject: (payload) =>
    req("/projects", { method: "POST", body: JSON.stringify(payload) }),
  getBoard: (projectId) => req(`/projects/${projectId}/board`),
  adopt: (suggestionId) =>
    req(`/suggestions/${suggestionId}/adopt`, { method: "POST" }),
  skip: (suggestionId) =>
    req(`/suggestions/${suggestionId}/skip`, { method: "POST" }),
  updateScore: (moduleId, value, speed = "internal") =>
    req(`/modules/${moduleId}/score`, {
      method: "POST",
      body: JSON.stringify({ value, speed }),
    }),
};
