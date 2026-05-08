const AUTH_STORAGE_KEY = "intraq_auth";

export function isAuthenticated() {
  return localStorage.getItem(AUTH_STORAGE_KEY) === "true";
}

export function setAuthenticated(value) {
  if (value) {
    localStorage.setItem(AUTH_STORAGE_KEY, "true");
    return;
  }

  localStorage.removeItem(AUTH_STORAGE_KEY);
}
