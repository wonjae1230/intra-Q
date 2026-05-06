const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

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

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  return request("/api/documents/upload", {
    method: "POST",
    body: formData, 
  });
}

export async function getDocument(documentId) {
  return request(`/api/documents/${documentId}`, {
    method: "GET",
  });
}

export async function getDocuments() {
  return request("/api/documents", {
    method: "GET",
  });
}

export async function askQuestion(question, documentIds = []) {
  return request("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      document_ids: documentIds,
    }),
  });
}

export { API_BASE_URL };
