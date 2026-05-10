import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { documents as initialDocuments } from "../data/mockData";
import {
  ActionButton,
  AppLayout,
  PageHeader,
  PageShell,
  Panel,
  PdfIcon,
  StatusBadge,
} from "../components/ui";
import { deleteDocument, getDocuments } from "../lib/api";

const USE_MOCK_FALLBACK = false;

function mapDocumentFromApi(item) {
  return {
    id: item.document_id ?? item.id,
    name: item.file_name ?? item.name ?? "unknown.pdf",
    size: item.size ?? "-",
    uploadedAt: item.uploaded_at?.slice?.(0, 10) ?? "-",
    pages: item.page_count ?? item.pages ?? "-",
    chunks: item.chunk_count ?? item.chunks ?? "-",
    status: item.status ?? "처리 완료",
  };
}

export default function DocumentManagementPage() {
  const navigate = useNavigate();

  const [documents, setDocuments] = useState([]);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterStatus, setFilterStatus] = useState("전체");
  const [loadError, setLoadError] = useState("");
  const [selectedDocumentIds, setSelectedDocumentIds] = useState([]);
  const [isDeleting, setIsDeleting] = useState(false);

  const filterButtons = ["전체", "처리 완료", "처리 중"];

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        setLoadError("");
        const response = await getDocuments();
        const rows =
          response?.data?.documents ?? response?.data ?? response?.documents ?? [];

        if (!Array.isArray(rows)) {
          throw new Error("문서 목록 응답 형식이 올바르지 않습니다.");
        }

        setDocuments(rows.map(mapDocumentFromApi));
      } catch (error) {
        setLoadError(error.message);
        setDocuments(USE_MOCK_FALLBACK ? initialDocuments : []);
      }
    };

    loadDocuments();
  }, []);

  const filteredDocuments = useMemo(() => {
    return documents.filter((doc) => {
      const matchesKeyword = doc.name
        .toLowerCase()
        .includes(searchKeyword.toLowerCase());

      const matchesStatus =
        filterStatus === "전체" || doc.status === filterStatus;

      return matchesKeyword && matchesStatus;
    });
  }, [documents, searchKeyword, filterStatus]);

  const filteredDocumentIds = useMemo(
    () => filteredDocuments.map((doc) => doc.id),
    [filteredDocuments]
  );

  const selectedCount = selectedDocumentIds.length;
  const allFilteredSelected =
    filteredDocumentIds.length > 0 &&
    filteredDocumentIds.every((id) => selectedDocumentIds.includes(id));

  const deleteDocumentsByIds = async (documentIds) => {
    if (documentIds.length === 0 || isDeleting) {
      return;
    }

    setIsDeleting(true);

    try {
      const results = await Promise.allSettled(
        documentIds.map((documentId) => deleteDocument(documentId))
      );
      const deletedIds = documentIds.filter(
        (_, index) => results[index].status === "fulfilled"
      );
      const failedCount = results.length - deletedIds.length;

      if (deletedIds.length > 0) {
        setDocuments((prevDocuments) =>
          prevDocuments.filter((doc) => !deletedIds.includes(doc.id))
        );
        setSelectedDocumentIds((prevSelectedIds) =>
          prevSelectedIds.filter((id) => !deletedIds.includes(id))
        );
      }

      if (failedCount > 0) {
        alert(`${failedCount}개 문서 삭제에 실패했습니다. 잠시 후 다시 시도해 주세요.`);
      }
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteDocument = async (documentId) => {
    const confirmed = window.confirm("이 문서를 삭제하시겠습니까?");

    if (!confirmed) {
      return;
    }

    await deleteDocumentsByIds([documentId]);
  };

  const handleToggleDocument = (documentId) => {
    setSelectedDocumentIds((prevSelectedIds) => {
      if (prevSelectedIds.includes(documentId)) {
        return prevSelectedIds.filter((id) => id !== documentId);
      }

      return [...prevSelectedIds, documentId];
    });
  };

  const handleToggleAllFiltered = () => {
    setSelectedDocumentIds((prevSelectedIds) => {
      if (allFilteredSelected) {
        return prevSelectedIds.filter((id) => !filteredDocumentIds.includes(id));
      }

      return Array.from(new Set([...prevSelectedIds, ...filteredDocumentIds]));
    });
  };

  const handleDeleteSelected = async () => {
    const confirmed = window.confirm(
      `선택한 ${selectedCount}개 문서를 삭제하시겠습니까?`
    );

    if (!confirmed) {
      return;
    }

    await deleteDocumentsByIds(selectedDocumentIds);
  };

  const handleDeleteAll = async () => {
    const confirmed = window.confirm(
      `전체 ${documents.length}개 문서를 모두 삭제하시겠습니까?`
    );

    if (!confirmed) {
      return;
    }

    await deleteDocumentsByIds(documents.map((doc) => doc.id));
  };

  return (
    <AppLayout>
      <PageShell className="h-[calc(100vh-136px)] min-h-0 overflow-hidden">
        <PageHeader
          title="문서 관리"
          description="업로드된 문서를 확인하고 질문에 사용할 문서를 관리하세요."
          action={
          <button
            type="button"
            onClick={() => navigate("/upload")}
            className="h-[42px] rounded-xl bg-blue-600 px-4 text-sm font-bold text-white transition hover:bg-blue-700"
          >
            새 문서 업로드
          </button>
          }
        />

        <Panel className="flex shrink-0 items-center gap-3.5 p-4">
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

          <div className="flex h-[46px] items-center gap-2">
            <button
              type="button"
              onClick={handleDeleteSelected}
              disabled={selectedCount === 0 || isDeleting}
              className="h-full rounded-[12px] border border-red-200 bg-white px-3.5 text-[13px] font-bold text-red-600 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              선택 삭제 {selectedCount > 0 ? `${selectedCount}` : ""}
            </button>

            <button
              type="button"
              onClick={handleDeleteAll}
              disabled={documents.length === 0 || isDeleting}
              className="h-full rounded-[12px] bg-red-600 px-3.5 text-[13px] font-bold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              전체 삭제
            </button>
          </div>
        </Panel>

        <Panel className="flex min-h-0 flex-1 flex-col overflow-hidden">
          <div className="grid h-[54px] shrink-0 grid-cols-[42px_340px_160px_90px_90px_130px_1fr] items-center gap-3 bg-slate-50 px-[18px] text-xs font-bold text-slate-500">
            <div className="flex items-center justify-center">
              <input
                type="checkbox"
                checked={allFilteredSelected}
                disabled={filteredDocuments.length === 0 || isDeleting}
                onChange={handleToggleAllFiltered}
                aria-label="현재 목록 전체 선택"
                className="h-4 w-4 rounded border-slate-300 accent-blue-600 disabled:cursor-not-allowed disabled:opacity-40"
              />
            </div>
            <div>문서명</div>
            <div>업로드 날짜</div>
            <div>페이지 수</div>
            <div>청크 수</div>
            <div>처리 상태</div>
            <div className="text-right">액션</div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto">
            {filteredDocuments.length > 0 ? (
              filteredDocuments.map((doc, index) => {
                const canUse = doc.status === "처리 완료";

                return (
                  <div
                    key={doc.id}
                    className={`grid h-[76px] grid-cols-[42px_340px_160px_90px_90px_130px_1fr] items-center gap-3 px-[18px] ${
                      index !== filteredDocuments.length - 1
                        ? "border-b border-slate-200"
                        : ""
                    }`}
                  >
                    <div className="flex items-center justify-center">
                      <input
                        type="checkbox"
                        checked={selectedDocumentIds.includes(doc.id)}
                        disabled={isDeleting}
                        onChange={() => handleToggleDocument(doc.id)}
                        aria-label={`${doc.name} 선택`}
                        className="h-4 w-4 rounded border-slate-300 accent-blue-600 disabled:cursor-not-allowed disabled:opacity-40"
                      />
                    </div>

                    <div className="flex min-w-0 items-center gap-2.5">
                      <PdfIcon />
                      <div className="min-w-0">
                        <p className="truncate text-sm font-bold">{doc.name}</p>
                        <p className="mt-0.5 text-xs text-slate-500">
                          {doc.size}
                        </p>
                      </div>
                    </div>

                    <div className="text-[13px] text-slate-600">
                      {doc.uploadedAt}
                    </div>

                    <div className="text-[13px] text-slate-600">
                      {doc.pages}페이지
                    </div>

                    <div className="text-[13px] text-slate-600">
                      {doc.chunks}청크
                    </div>

                    <StatusBadge status={doc.status} />

                    <div className="flex justify-end gap-2">
                      <ActionButton onClick={() => navigate("/documents/detail")}>
                        보기
                      </ActionButton>

                      <ActionButton
                        variant="primary"
                        disabled={!canUse}
                        onClick={() => navigate("/chat")}
                      >
                        질문에 사용
                      </ActionButton>

                      <ActionButton
                        variant="danger"
                        onClick={() => handleDeleteDocument(doc.id)}
                      >
                        삭제
                      </ActionButton>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="flex h-full min-h-[220px] flex-col items-center justify-center gap-2 text-center">
                <p className="text-sm font-bold text-slate-700">
                  검색 결과가 없습니다.
                </p>
                <p className="text-xs text-slate-500">
                  {loadError || "다른 문서명으로 검색하거나 필터를 변경해보세요."}
                </p>
              </div>
            )}
          </div>
        </Panel>
      </PageShell>
    </AppLayout>
  );
}
