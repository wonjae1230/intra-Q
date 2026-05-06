import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import ChatPage from "./pages/ChatPage";
import DocumentUploadPage from "./pages/DocumentUploadPage";
import DocumentManagementPage from "./pages/DocumentManagementPage";
import DocumentDetailPage from "./pages/DocumentDetailPage";
import EmptyStatePage from "./pages/EmptyStatePage";
import AnswerNotFoundPage from "./pages/AnswerNotFoundPage";
import ServerErrorPage from "./pages/ServerErrorPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<EmptyStatePage />} />
        <Route path="/upload" element={<DocumentUploadPage />} />
        <Route path="/documents" element={<DocumentManagementPage />} />
        <Route path="/documents/detail" element={<DocumentDetailPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/error/not-found" element={<AnswerNotFoundPage />} />
        <Route path="/error/server" element={<ServerErrorPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;