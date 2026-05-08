import { Navigate, createBrowserRouter } from "react-router-dom";

import ChatPage from "../pages/ChatPage";
import DocumentUploadPage from "../pages/DocumentUploadPage";
import DocumentManagementPage from "../pages/DocumentManagementPage";
import DocumentDetailPage from "../pages/DocumentDetailPage";
import EmptyStatePage from "../pages/EmptyStatePage";
import AnswerNotFoundPage from "../pages/AnswerNotFoundPage";
import ServerErrorPage from "../pages/ServerErrorPage";
import { LoginPage, SignupPage } from "../pages/AuthPage";
import { ProtectedRoute, PublicOnlyRoute } from "./guards";

export const router = createBrowserRouter([
  { path: "/", element: <EmptyStatePage /> },
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
