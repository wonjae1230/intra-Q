import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AppLayout, PdfIcon, StatusBadge } from "../components/ui";
import { uploadDocument } from "../lib/api";

const stages = [
  "업로드 완료",
  "텍스트 추출 중",
  "청크 분할 중",
  "임베딩 생성 중",
  "처리 완료",
];

function formatFileSize(size) {
  const mb = size / 1024 / 1024;

  if (mb >= 1) {
    return `${mb.toFixed(1)} MB`;
  }

  return `${Math.round(size / 1024)} KB`;
}

export default function DocumentUploadPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [documents, setDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const processFiles = async (files) => {
    if (isUploading) {
      return;
    }

    const pdfFiles = files.filter(
      (file) =>
        file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")
    );

    if (pdfFiles.length === 0) {
      return;
    }

    setIsUploading(true);
    setUploadError("");

    const placeholders = pdfFiles.map((file, index) => ({
      tempId: `uploading-${file.name}-${file.lastModified}-${index}`,
      name: file.name,
      size: formatFileSize(file.size),
      uploadedTime: "업로드 중",
      pages: "-",
      chunks: "-",
      status: "처리 중",
      progress: 40,
    }));

    setDocuments((prevDocuments) => [...placeholders, ...prevDocuments]);

    const results = await Promise.allSettled(
      pdfFiles.map(async (file, index) => {
        const response = await uploadDocument(file);
        const data = response?.data ?? response ?? {};

        return {
          tempId: placeholders[index].tempId,
          id: data.document_id ?? placeholders[index].tempId,
          name: data.file_name || file.name,
          size: formatFileSize(file.size),
          uploadedTime: "방금",
          pages: data.page_count ?? "-",
          chunks: data.chunk_count ?? "-",
          status: "처리 완료",
          progress: 100,
        };
      })
    );

    const resolvedDocuments = results.map((result, index) => {
      if (result.status === "fulfilled") {
        return result.value;
      }

      return {
        tempId: placeholders[index].tempId,
        id: placeholders[index].tempId,
        name: placeholders[index].name,
        size: placeholders[index].size,
        uploadedTime: "실패",
        pages: "-",
        chunks: "-",
        status: "업로드 실패",
        progress: 0,
      };
    });

    setDocuments((prevDocuments) =>
      prevDocuments.map((doc) => {
        const resolved = resolvedDocuments.find((item) => item.tempId === doc.tempId);

        if (!resolved) {
          return doc;
        }

        return { ...resolved };
      })
    );

    const hasFailure = results.some((result) => result.status === "rejected");

    if (hasFailure) {
      setUploadError(
        "일부 파일 업로드에 실패했습니다. 파일 형식과 서버 상태를 확인해 주세요."
      );
    }

    setIsUploading(false);
  };

  const handleFileChange = async (event) => {
    const files = Array.from(event.target.files || []);
    event.target.value = "";
    await processFiles(files);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    setIsDragging(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (event) => {
    event.preventDefault();
    setIsDragging(false);

    const files = Array.from(event.dataTransfer.files || []);
    await processFiles(files);
  };

  return (
    <AppLayout>
      <div className="mx-auto flex min-h-[calc(100vh-136px)] max-w-[1296px] flex-col gap-6">
        <header className="flex items-center gap-6">
          <div className="flex-1">
            <h1 className="text-[34px] font-bold tracking-normal">
              문서 업로드
            </h1>
            <p className="mt-2 text-[15px] text-slate-500">
              PDF 문서를 업로드하면 질문에 사용할 수 있도록 자동 분석됩니다.
            </p>
          </div>

          <span className="rounded-full border border-blue-200 bg-blue-50 px-[13px] py-[9px] text-[13px] font-bold text-blue-600">
            문서 분석 준비
          </span>
        </header>

        <div className="flex flex-1 gap-6">
          <section className="flex w-[470px] flex-col gap-[18px] rounded-3xl border border-slate-200 bg-white p-[22px]">
            <h2 className="text-lg font-bold">PDF 업로드</h2>

            <button
              type="button"
              onClick={handleFileSelect}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`flex h-[330px] flex-col items-center justify-center gap-3.5 rounded-[22px] border border-dashed p-7 text-center transition ${
                isDragging
                  ? "border-blue-500 bg-blue-50"
                  : "border-blue-200 bg-slate-50 hover:bg-blue-50"
              }`}
            >
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-50 font-mono text-[34px] font-extrabold text-blue-600">
                ↑
              </div>
              <p className="text-[17px] font-bold">
                PDF 파일을 여기에 놓으세요
              </p>
              <p className="text-sm text-slate-500">
                드래그 앤 드롭하거나 파일 선택 버튼을 사용하세요
              </p>
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              multiple
              className="hidden"
              onChange={handleFileChange}
            />

            <button
              type="button"
              onClick={handleFileSelect}
              disabled={isUploading}
              className="h-[50px] rounded-[14px] bg-blue-600 text-[15px] font-bold text-white transition hover:bg-blue-700"
            >
              {isUploading ? "업로드 중..." : "파일 선택"}
            </button>

            {uploadError && (
              <p className="text-sm font-semibold text-red-600">{uploadError}</p>
            )}

            <div className="rounded-[18px] border border-blue-200 bg-blue-50 p-4">
              <h3 className="text-sm font-bold text-blue-600">처리 단계</h3>

              <div className="mt-3 flex flex-wrap gap-2">
                {stages.map((stage) => (
                  <StatusBadge key={stage} status={stage} />
                ))}
              </div>
            </div>
          </section>

          <section className="flex flex-1 flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-[22px]">
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <h2 className="text-xl font-bold">업로드된 문서</h2>
                <p className="mt-1 text-[13px] text-slate-500">
                  문서 분석이 끝나면 질문에 사용할 수 있습니다.
                </p>
              </div>

              <span className="rounded-full bg-slate-100 px-3 py-1.5 font-mono text-xs font-bold text-slate-600">
                {documents.length} files
              </span>
            </div>

            <div className="flex flex-col gap-3.5 overflow-y-auto pr-1">
              {documents.map((doc) => (
                <article
                  key={doc.id}
                  className="rounded-[18px] border border-slate-200 bg-slate-50 p-[18px]"
                >
                  <div className="mb-3.5 flex items-center gap-3">
                    <PdfIcon size="lg" />

                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[15px] font-bold">
                        {doc.name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {doc.size} · {doc.uploadedTime} 업로드
                      </p>
                    </div>

                    <StatusBadge status={doc.status} />
                  </div>

                  <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                    <div
                      className="h-full rounded-full bg-blue-600 transition-all"
                      style={{ width: `${doc.progress}%` }}
                    />
                  </div>
                </article>
              ))}
            </div>

            <div className="mt-auto rounded-[18px] border border-slate-200 bg-slate-50 p-4">
              <h3 className="text-sm font-bold">다음 단계</h3>
              <p className="mt-2 text-[13px] text-slate-500">
                처리가 완료된 문서는 관리 화면에서 확인하거나 바로 질문에 사용할
                수 있습니다.
              </p>

              <div className="mt-3 flex gap-2.5">
                <button
                  type="button"
                  onClick={() => navigate("/documents")}
                  className="h-[42px] flex-1 rounded-xl border border-slate-300 bg-white text-sm font-bold text-slate-700 transition hover:bg-slate-50"
                >
                  문서 관리로 이동
                </button>

                <button
                  type="button"
                  onClick={() => navigate("/chat")}
                  className="h-[42px] flex-1 rounded-xl bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700"
                >
                  질문하러 가기
                </button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </AppLayout>
  );
}