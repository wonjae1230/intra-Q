import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";

import ChatPage from "./pages/ChatPage";
import DocumentUploadPage from "./pages/DocumentUploadPage";
import DocumentManagementPage from "./pages/DocumentManagementPage";
import DocumentDetailPage from "./pages/DocumentDetailPage";
import EmptyStatePage from "./pages/EmptyStatePage";
import ErrorStatePage from "./pages/ErrorStatePage";

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#F8FAFC]">
        <nav className="border-b border-slate-200 bg-white px-6 py-3">
          <div className="mx-auto flex max-w-[1296px] items-center gap-4">
            <Link to="/" className="mr-4 text-lg font-extrabold text-blue-600">
              Intra-Q
            </Link>

            <Link to="/" className="text-sm font-bold text-slate-600 hover:text-blue-600">
              첫 화면
            </Link>
            <Link to="/chat" className="text-sm font-bold text-slate-600 hover:text-blue-600">
              챗봇
            </Link>
            <Link to="/upload" className="text-sm font-bold text-slate-600 hover:text-blue-600">
              문서 업로드
            </Link>
            <Link to="/documents" className="text-sm font-bold text-slate-600 hover:text-blue-600">
              문서 관리
            </Link>
            <Link to="/documents/detail" className="text-sm font-bold text-slate-600 hover:text-blue-600">
              출처 상세
            </Link>
            <Link to="/error" className="text-sm font-bold text-slate-600 hover:text-blue-600">
              에러 상태
            </Link>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<EmptyStatePage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/upload" element={<DocumentUploadPage />} />
          <Route path="/documents" element={<DocumentManagementPage />} />
          <Route path="/documents/detail" element={<DocumentDetailPage />} />
          <Route path="/error" element={<ErrorStatePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;