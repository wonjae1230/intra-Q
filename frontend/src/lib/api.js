const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const TOKEN_KEY = "intra_q_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(extra = {}) {
  const token = getToken();
  return token
    ? { Authorization: `Bearer ${token}`, ...extra }
    : { ...extra };
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const contentType = response.headers.get("content-type") || "";
  const isJson = contentType.includes("application/json");
  const payload = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const detail =
      (isJson && (payload?.detail || payload?.message)) ||
      `Request failed: ${response.status}`;
    throw new Error(detail);
  }

  return payload;
}

export async function register(email, password, nickname) {
  return request("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, nickname }),
  });
}

export async function login(email, password) {
  const res = await request("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  setToken(res.data.access_token);
  return res;
}

export function logout() {
  removeToken();
}

export async function getMe() {
  return request("/api/auth/me", {
    method: "GET",
    headers: authHeaders(),
  });
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  return request("/api/documents/upload", {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
}

export async function getDocument(documentId) {
  return request(`/api/documents/${documentId}`, {
    method: "GET",
    headers: authHeaders(),
  });
}

export async function getDocuments() {
  return request("/api/documents", {
    method: "GET",
    headers: authHeaders(),
  });
}

export async function deleteDocument(documentId) {
  return request(`/api/documents/${documentId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
}

export async function clarifyQuestion(question, documentIds = []) {
  return request("/api/chat/clarify", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ question, document_ids: documentIds }),
  });
}

export async function askQuestion(question, documentIds = [], approachHint = null) {
  return request("/api/chat", {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({
      question,
      document_ids: documentIds,
      ...(approachHint ? { approach_hint: approachHint } : {}),
    }),
  });
}

export async function getRecentChatMessages(limit = 50) {
  const params = new URLSearchParams({ limit: String(limit) });
  return request(`/api/chat/recent?${params.toString()}`, {
    method: "GET",
    headers: authHeaders(),
  });
}

export { API_BASE_URL };
