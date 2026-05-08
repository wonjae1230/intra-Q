import { Navigate, Outlet, createBrowserRouter } from "react-router-dom";

import ChatPage from "../pages/ChatPage";
import DocumentUploadPage from "../pages/DocumentUploadPage";
import DocumentManagementPage from "../pages/DocumentManagementPage";
import DocumentDetailPage from "../pages/DocumentDetailPage";
import EmptyStatePage from "../pages/EmptyStatePage";
import AnswerNotFoundPage from "../pages/AnswerNotFoundPage";
import ServerErrorPage from "../pages/ServerErrorPage";
import { LoginPage, SignupPage } from "../pages/AuthPage";

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

function PublicOnlyRoute() {
  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}

function ProtectedRoute() {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

export const router = createBrowserRouter([
  {
    element: <PublicOnlyRoute />,
    children: [
      { path: "/login", element: <LoginPage /> },
      { path: "/signup", element: <SignupPage /> },
    ],
  },
  {
    element: <ProtectedRoute />,
    children: [
      { path: "/", element: <EmptyStatePage /> },
      { path: "/upload", element: <DocumentUploadPage /> },
      { path: "/documents", element: <DocumentManagementPage /> },
      { path: "/documents/detail", element: <DocumentDetailPage /> },
      { path: "/chat", element: <ChatPage /> },
      { path: "/error/not-found", element: <AnswerNotFoundPage /> },
      { path: "/error/server", element: <ServerErrorPage /> },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
