import { useMemo, useState } from "react";

const initialDocuments = [
  {
    name: "인사규정.pdf",
    date: "2026-05-04",
    pages: "24페이지",
    chunks: "86청크",
    status: "완료",
    canUse: true,
  },
  {
    name: "보안정책.pdf",
    date: "2026-05-03",
    pages: "12페이지",
    chunks: "41청크",
    status: "완료",
    canUse: true,
  },
  {
    name: "온보딩가이드.pdf",
    date: "2026-05-02",
    pages: "18페이지",
    chunks: "52청크",
    status: "처리중",
    canUse: false,
  },
];

function PdfIcon() {
  return (
    <div className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-red-100 font-mono text-[10px] font-extrabold text-red-600">
      PDF
    </div>
  );
}

function StatusBadge({ status }) {
  const isComplete = status === "완료";

  return (
    <span
      className={`inline-flex w-[120px] items-center gap-1.5 rounded-full px-2.5 py-1.5 text-xs font-bold ${
        isComplete
          ? "bg-emerald-50 text-emerald-600"
          : "bg-amber-50 text-amber-600"
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          isComplete ? "bg-emerald-600" : "bg-amber-600"
        }`}
      />
      {status}
    </span>
  );
}

function ActionButton({ children, variant = "outline", disabled, onClick }) {
  const styles = {
    outline: "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50",
    primary: "bg-blue-600 text-white hover:bg-blue-700",
    danger: "border border-red-200 bg-white text-red-600 hover:bg-red-50",
  };

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`h-[34px] rounded-[10px] px-3 text-xs font-bold transition disabled:cursor-not-allowed disabled:opacity-45 ${styles[variant]}`}
    >
      {children}
    </button>
  );
}

export default function DocumentManagementPage() {
  const [documents, setDocuments] = useState(initialDocuments);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterStatus, setFilterStatus] = useState("전체");
  const [selectedDocument, setSelectedDocument] = useState(null);

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      const matchesKeyword = doc.name
        .toLowerCase()
        .includes(searchKeyword.toLowerCase());

      const matchesStatus =
        filterStatus === "전체" ||
        (filterStatus === "처리 완료" && doc.status === "완료") ||
        (filterStatus === "처리 중" && doc.status === "처리중");

      return matchesKeyword && matchesStatus;
    });
  }, [documents, searchKeyword, filterStatus]);

  const handleDeleteDocument = (documentName) => {
    setDocuments((prevDocuments) =>
      prevDocuments.filter((doc) => doc.name !== documentName)
    );

    if (selectedDocument?.name === documentName) {
      setSelectedDocument(null);
    }
  };

  const handleUseDocument = (doc) => {
    if (!doc.canUse) {
      return;
    }

    setSelectedDocument(doc);
  };

  const filterButtons = ["전체", "처리 완료", "처리 중"];

  return (
    <main className="min-h-screen bg-[#F8FAFC] p-6 font-sans text-slate-950">
      <div className="mx-auto flex h-[800px] max-w-[1296px] flex-col gap-6">
        <header className="flex items-center gap-5">
          <div className="flex-1">
            <h1 className="text-[34px] font-bold tracking-normal">
              문서 관리
            </h1>
            <p className="mt-2 text-[15px] text-slate-500">
              업로드된 PDF 문서를 검색하고, 질문에 사용할 문서를 관리합니다.
            </p>
          </div>

          <button
            type="button"
            className="h-[42px] rounded-xl bg-blue-600 px-4 text-sm font-bold text-white transition hover:bg-blue-700"
          >
            새 문서 업로드
          </button>
        </header>

        <section className="flex items-center gap-3.5 rounded-[20px] border border-slate-200 bg-white p-4">
          <div className="flex h-[46px] flex-1 items-center gap-2.5 rounded-[14px] border border-slate-300 bg-slate-50 px-4">
            <span className="font-mono text-lg font-bold text-slate-500">
              ⌕
            </span>
            <input
              value={searchKeyword}
              onChange={(event) => setSearchKeyword(event.target.value)}
              className="flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400"
              placeholder="문서명으로 검색"
            />
          </div>

          <div className="flex h-[46px] items-center gap-1.5 rounded-[14px] bg-slate-100 p-1">
            {filterButtons.map((filter) => {
              const isActive = filterStatus === filter;

              return (
                <button
                  key={filter}
                  type="button"
                  onClick={() => setFilterStatus(filter)}
                  className={`h-full rounded-[10px] px-3.5 text-[13px] transition ${
                    isActive
                      ? "border border-slate-200 bg-white font-bold text-slate-950"
                      : "font-semibold text-slate-500 hover:text-slate-800"
                  }`}
                >
                  {filter}
                </button>
              );
            })}
          </div>
        </section>

        {selectedDocument && (
          <section className="flex items-center gap-3 rounded-[18px] border border-blue-200 bg-blue-50 px-4 py-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 font-mono text-xs font-bold text-white">
              Q
            </div>
            <p className="flex-1 text-sm font-semibold text-blue-700">
              현재 질문에 사용할 문서로{" "}
              <span className="font-extrabold">{selectedDocument.name}</span>
              을 선택했습니다.
            </p>
            <button
              type="button"
              onClick={() => setSelectedDocument(null)}
              className="text-xs font-bold text-blue-600"
            >
              선택 해제
            </button>
          </section>
        )}

        <section className="overflow-hidden rounded-3xl border border-slate-200 bg-white">
          <div className="grid h-[54px] grid-cols-[360px_170px_100px_100px_140px_1fr] items-center gap-3 bg-slate-50 px-[18px] text-xs font-bold text-slate-500">
            <div>문서명</div>
            <div>업로드 날짜</div>
            <div>페이지 수</div>
            <div>청크 수</div>
            <div>처리 상태</div>
            <div className="text-right">액션</div>
          </div>

          {filteredDocuments.length > 0 ? (
            filteredDocuments.map((doc, index) => (
              <div
                key={doc.name}
                className={`grid h-[76px] grid-cols-[360px_170px_100px_100px_140px_1fr] items-center gap-3 px-[18px] ${
                  index !== filteredDocuments.length - 1
                    ? "border-b border-slate-200"
                    : ""
                }`}
              >
                <div className="flex min-w-0 items-center gap-2.5">
                  <PdfIcon />
                  <span className="truncate text-sm font-bold">
                    {doc.name}
                  </span>
                </div>

                <div className="text-[13px] text-slate-600">{doc.date}</div>
                <div className="text-[13px] text-slate-600">{doc.pages}</div>
                <div className="text-[13px] text-slate-600">{doc.chunks}</div>

                <StatusBadge status={doc.status} />

                <div className="flex justify-end gap-2">
                  <ActionButton onClick={() => setSelectedDocument(doc)}>
                    보기
                  </ActionButton>

                  <ActionButton
                    variant="primary"
                    disabled={!doc.canUse}
                    onClick={() => handleUseDocument(doc)}
                  >
                    질문에 사용
                  </ActionButton>

                  <ActionButton
                    variant="danger"
                    onClick={() => handleDeleteDocument(doc.name)}
                  >
                    삭제
                  </ActionButton>
                </div>
              </div>
            ))
          ) : (
            <div className="flex h-[220px] flex-col items-center justify-center gap-2 text-center">
              <p className="text-sm font-bold text-slate-700">
                검색 결과가 없습니다.
              </p>
              <p className="text-xs text-slate-500">
                다른 문서명으로 검색하거나 필터를 변경해보세요.
              </p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}