import { useRef, useState } from "react";

const statusExamples = [
  ["업로드 완료", "bg-slate-100 text-slate-600"],
  ["텍스트 추출 중", "bg-amber-50 text-amber-600"],
  ["청크 분할 중", "bg-indigo-50 text-indigo-600"],
  ["임베딩 생성 중", "bg-blue-50 text-blue-600"],
  ["처리 완료", "bg-emerald-50 text-emerald-600"],
];

const initialDocuments = [
  {
    name: "인사규정.pdf",
    meta: "1.8 MB · 오늘 09:12 업로드",
    status: "처리 완료",
    statusClass: "bg-emerald-50 text-emerald-600",
    dotClass: "bg-emerald-600",
    progress: 100,
    progressClass: "bg-emerald-600",
  },
  {
    name: "보안정책.pdf",
    meta: "1.2 MB · 오늘 09:18 업로드",
    status: "임베딩 생성 중",
    statusClass: "bg-blue-50 text-blue-600",
    dotClass: "bg-blue-600",
    progress: 75,
    progressClass: "bg-blue-600",
  },
  {
    name: "출장비규정.pdf",
    meta: "860 KB · 오늘 09:21 업로드",
    status: "텍스트 추출 중",
    statusClass: "bg-amber-50 text-amber-600",
    dotClass: "bg-amber-600",
    progress: 34,
    progressClass: "bg-amber-600",
  },
];

function formatFileSize(size) {
  const mb = size / 1024 / 1024;

  if (mb >= 1) {
    return `${mb.toFixed(1)} MB`;
  }

  return `${Math.round(size / 1024)} KB`;
}

function StatusBadge({ label, className, dotClassName }) {
  return (
    <span
      className={`inline-flex w-fit items-center gap-1.5 rounded-full px-2.5 py-1.5 text-xs font-bold ${className}`}
    >
      {dotClassName ? (
        <span className={`h-1.5 w-1.5 rounded-full ${dotClassName}`} />
      ) : null}
      {label}
    </span>
  );
}

function PdfIcon() {
  return (
    <div className="flex h-[42px] w-[42px] items-center justify-center rounded-xl bg-red-100 font-mono text-[11px] font-extrabold text-red-600">
      PDF
    </div>
  );
}

function DocumentCard({ doc }) {
  return (
    <article className="flex flex-col gap-3.5 rounded-[18px] border border-slate-200 bg-slate-50 p-[18px]">
      <div className="flex items-center gap-3">
        <PdfIcon />

        <div className="min-w-0 flex-1">
          <h3 className="truncate text-[15px] font-bold text-slate-950">
            {doc.name}
          </h3>
          <p className="mt-1 text-xs text-slate-500">{doc.meta}</p>
        </div>

        <StatusBadge
          label={doc.status}
          className={doc.statusClass}
          dotClassName={doc.dotClass}
        />
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-slate-200">
        <div
          className={`h-full rounded-full transition-all ${doc.progressClass}`}
          style={{ width: `${doc.progress}%` }}
        />
      </div>
    </article>
  );
}

export default function DocumentUploadPage() {
  const fileInputRef = useRef(null);
  const [documents, setDocuments] = useState(initialDocuments);

  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event) => {
    const files = Array.from(event.target.files || []);
    const pdfFiles = files.filter((file) => file.type === "application/pdf");

    const newDocuments = pdfFiles.map((file) => ({
      name: file.name,
      meta: `${formatFileSize(file.size)} · 방금 업로드`,
      status: "업로드 완료",
      statusClass: "bg-slate-100 text-slate-600",
      dotClass: "bg-slate-500",
      progress: 10,
      progressClass: "bg-slate-500",
    }));

    setDocuments((prevDocuments) => [...newDocuments, ...prevDocuments]);
    event.target.value = "";
  };

  return (
    <main className="min-h-screen bg-[#F8FAFC] p-6 font-sans text-slate-950">
      <div className="mx-auto flex h-[800px] max-w-[1296px] flex-col gap-6">
        <header className="flex items-center gap-6">
          <div className="flex-1">
            <h1 className="text-[34px] font-bold tracking-normal text-slate-950">
              문서 업로드
            </h1>
            <p className="mt-2 max-w-3xl text-[15px] leading-relaxed text-slate-500">
              PDF 문서를 업로드하면 텍스트 추출, 청크 분할, 임베딩 생성 후
              질문에 사용할 수 있습니다.
            </p>
          </div>

          <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-[13px] py-[9px] text-[13px] font-bold text-blue-600">
            <span className="h-2 w-2 rounded-full bg-blue-600" />
            AI 검색 인덱싱
          </div>
        </header>

        <div className="flex flex-1 gap-6">
          <section className="flex w-[470px] flex-col gap-[18px] rounded-3xl border border-slate-200 bg-white p-[22px]">
            <h2 className="text-lg font-bold">새 PDF 추가</h2>

            <button
              type="button"
              onClick={handleFileButtonClick}
              className="flex h-[330px] flex-col items-center justify-center gap-3.5 rounded-[22px] border border-dashed border-blue-200 bg-slate-50 p-7 text-center transition hover:bg-blue-50"
            >
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-50 font-mono text-[34px] font-extrabold text-blue-600">
                ↑
              </div>
              <p className="text-[17px] font-bold">
                PDF 파일을 여기에 드래그 앤 드롭
              </p>
              <p className="text-sm text-slate-500">
                또는 아래 버튼으로 파일을 선택하세요
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
              onClick={handleFileButtonClick}
              className="h-[50px] rounded-[14px] bg-blue-600 text-[15px] font-bold text-white transition hover:bg-blue-700"
            >
              파일 선택
            </button>

            <div className="rounded-[18px] border border-blue-200 bg-blue-50 p-4">
              <h3 className="text-sm font-bold text-blue-600">
                처리 파이프라인
              </h3>

              <div className="mt-2 flex flex-col gap-2 text-xs leading-relaxed text-slate-700">
                <p>1. 업로드 완료 → 2. 텍스트 추출 → 3. 청크 분할</p>
                <p>4. 임베딩 생성 → 5. 처리 완료</p>
              </div>

              <div className="mt-3 flex flex-col gap-2">
                <div className="flex flex-wrap gap-2">
                  {statusExamples.slice(0, 2).map(([label, className]) => (
                    <StatusBadge
                      key={label}
                      label={label}
                      className={className}
                    />
                  ))}
                </div>

                <div className="flex flex-wrap gap-2">
                  {statusExamples.slice(2).map(([label, className]) => (
                    <StatusBadge
                      key={label}
                      label={label}
                      className={className}
                    />
                  ))}
                </div>
              </div>
            </div>
          </section>

          <section className="flex flex-1 flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-[22px]">
            <div className="flex items-center gap-3">
              <div className="flex-1">
                <h2 className="text-xl font-bold">업로드된 문서 리스트</h2>
                <p className="mt-1 text-[13px] text-slate-500">
                  문서별 처리 상태와 진행률을 확인하세요.
                </p>
              </div>

              <span className="rounded-full bg-slate-100 px-3 py-1.5 font-mono text-xs font-bold text-slate-600">
                {documents.length} files
              </span>
            </div>

            <div className="flex flex-col gap-3.5 overflow-y-auto pr-1">
              {documents.map((doc, index) => (
                <DocumentCard key={`${doc.name}-${index}`} doc={doc} />
              ))}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}