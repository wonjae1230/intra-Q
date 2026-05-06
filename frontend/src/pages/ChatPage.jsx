import { useRef, useState } from "react";

const initialDocs = [
  {
    name: "인사규정.pdf",
    meta: "24 pages · 1.8 MB",
    status: "완료",
    tone: "green",
  },
  {
    name: "보안정책.pdf",
    meta: "18 pages · 1.2 MB",
    status: "분석중",
    tone: "amber",
  },
];

const initialSources = [
  {
    doc: "인사규정.pdf",
    page: "p. 18",
    score: "0.92",
    text: "출산전후휴가는 90일로 하며, 출산 후 45일 이상을 보장한다...",
  },
  {
    doc: "인사규정.pdf",
    page: "p. 21",
    score: "0.88",
    text: "다태아 임신의 경우 출산전후휴가는 총 120일로 적용한다...",
  },
  {
    doc: "보안정책.pdf",
    page: "p. 04",
    score: "0.61",
    text: "개인정보 및 민감정보 조회 시 접근 권한과 감사 로그를 확인한다...",
  },
];

function StatusBadge({ status, tone }) {
  const styles =
    tone === "green"
      ? "bg-emerald-50 text-emerald-600"
      : "bg-amber-50 text-amber-600";

  return (
    <span
      className={`inline-flex w-fit items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold ${styles}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}

function PdfIcon() {
  return (
    <div className="flex h-[34px] w-[34px] items-center justify-center rounded-[10px] bg-red-100 text-[10px] font-extrabold text-red-600">
      PDF
    </div>
  );
}

function SourceCard({ source }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-3.5">
      <div className="flex items-center gap-2">
        <p className="text-[13px] font-bold">{source.doc}</p>
        <div className="flex-1" />
        <span className="rounded-full bg-blue-50 px-2 py-1 font-mono text-[11px] font-bold text-blue-600">
          {source.score}
        </span>
      </div>
      <p className="mt-2.5 font-mono text-xs font-bold text-slate-500">
        {source.page}
      </p>
      <p className="mt-2.5 text-xs leading-relaxed text-slate-600">
        {source.text}
      </p>
    </article>
  );
}

export default function ChatPage() {
  const fileInputRef = useRef(null);

  const [docs, setDocs] = useState(initialDocs);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: "user",
      text: "출산휴가는 며칠이야?",
    },
    {
      id: 2,
      type: "ai",
      text: "출산전후휴가는 총 90일입니다. 이 중 출산 후 휴가 기간은 최소 45일 이상 확보되어야 하며, 다태아의 경우 총 120일로 확대됩니다.",
      evidence: "근거: 인사규정.pdf · 제7장 휴가 및 복무",
      sources: initialSources,
    },
  ]);

  const handleFileButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event) => {
    const files = Array.from(event.target.files || []);

    const pdfFiles = files.filter((file) => file.type === "application/pdf");

    const newDocs = pdfFiles.map((file) => ({
      name: file.name,
      meta: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
      status: "분석중",
      tone: "amber",
    }));

    setDocs((prevDocs) => [...newDocs, ...prevDocs]);

    event.target.value = "";
  };

  const handleSendMessage = () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      return;
    }

    const userMessage = {
      id: Date.now(),
      type: "user",
      text: trimmedQuestion,
    };

    const aiMessage = {
      id: Date.now() + 1,
      type: "ai",
      text: "현재는 UI 구현 단계입니다. 이후 백엔드 API와 연결하면 업로드된 PDF를 기반으로 답변을 생성할 수 있습니다.",
      evidence: "근거: API 연결 전 임시 응답",
      sources: [],
    };

    setMessages((prevMessages) => [...prevMessages, userMessage, aiMessage]);
    setQuestion("");
  };

  const handleEnterKeyDown = (event) => {
    if (event.key === "Enter") {
      handleSendMessage();
    }
  };

  return (
    <main className="min-h-screen bg-[#F8FAFC] p-6 font-sans text-slate-950">
      <div className="flex h-[800px] gap-6">
        <aside className="flex w-[360px] flex-col gap-5 rounded-3xl border border-slate-200 bg-white p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 font-mono text-[22px] font-extrabold text-white">
              Q
            </div>

            <div>
              <h1 className="text-lg font-bold">Intra-Q</h1>
              <p className="text-[13px] text-slate-500">
                기업 내부 문서 Q&amp;A 봇
              </p>
            </div>
          </div>

          <section className="flex flex-col gap-3 rounded-[18px] border border-slate-200 bg-slate-50 p-4">
            <h2 className="text-[15px] font-bold">PDF 업로드</h2>

            <button
              type="button"
              onClick={handleFileButtonClick}
              className="flex h-[150px] flex-col items-center justify-center gap-2.5 rounded-2xl border border-blue-200 bg-white p-4 transition hover:bg-blue-50"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-blue-50 font-mono text-2xl font-bold text-blue-600">
                ↑
              </div>
              <p className="text-sm font-bold">PDF를 드래그하거나 클릭</p>
              <p className="text-xs text-slate-500">최대 50MB · PDF only</p>
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
              className="h-10 rounded-xl bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700"
            >
              문서 선택
            </button>
          </section>

          <section className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <h2 className="text-[15px] font-bold">업로드된 문서</h2>
              <div className="h-px flex-1" />
              <span className="font-mono text-[13px] font-bold text-slate-500">
                {docs.length}
              </span>
            </div>

            <div className="flex flex-col gap-3 overflow-y-auto pr-1">
              {docs.map((doc, index) => (
                <article
                  key={`${doc.name}-${index}`}
                  className="flex flex-col gap-2.5 rounded-2xl border border-slate-200 bg-white p-3.5"
                >
                  <div className="flex items-center gap-2.5">
                    <PdfIcon />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-bold">{doc.name}</p>
                      <p className="text-xs text-slate-500">{doc.meta}</p>
                    </div>
                  </div>

                  <StatusBadge status={doc.status} tone={doc.tone} />
                </article>
              ))}
            </div>
          </section>

          <div className="mt-auto rounded-2xl border border-blue-200 bg-blue-50 p-3.5">
            <p className="text-[13px] font-bold text-blue-600">답변 품질 팁</p>
            <p className="mt-1.5 text-xs leading-relaxed text-slate-700">
              질문에 제도명이나 문서명을 함께 넣으면 더 정확한 출처를 찾습니다.
            </p>
          </div>
        </aside>

        <section className="flex flex-1 flex-col gap-[18px]">
          <header className="flex items-center gap-4 px-0.5 py-1">
            <div className="flex-1">
              <h2 className="text-2xl font-bold">문서 기반 Q&amp;A</h2>
              <p className="text-sm text-slate-500">
                업로드한 사내 문서를 근거로 답변과 출처를 함께 확인합니다.
              </p>
            </div>

            <div className="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-2 text-[13px] font-semibold text-blue-600">
              <span className="h-2 w-2 rounded-full bg-blue-600" />
              {docs.length}개 문서 연결됨
            </div>
          </header>

          <div className="flex flex-1 flex-col gap-[18px] rounded-3xl border border-slate-200 bg-white p-6">
            <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-3">
              <div className="flex h-[34px] w-[34px] items-center justify-center rounded-[10px] bg-blue-50 font-mono text-[13px] font-extrabold text-blue-600">
                AI
              </div>

              <div>
                <p className="text-sm font-bold">인사·보안 문서 질의 세션</p>
                <p className="text-xs text-slate-500">
                  응답은 업로드된 PDF 출처를 기준으로 생성됩니다.
                </p>
              </div>
            </div>

            <div className="flex flex-1 flex-col gap-[18px] overflow-y-auto pr-1">
              {messages.map((message) => {
                if (message.type === "user") {
                  return (
                    <div key={message.id} className="flex justify-end">
                      <div className="max-w-[420px] rounded-[18px] rounded-br bg-blue-600 px-4 py-3.5 text-[15px] leading-relaxed text-white">
                        {message.text}
                      </div>
                    </div>
                  );
                }

                return (
                  <div key={message.id} className="flex gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-950 font-mono text-[13px] font-extrabold text-white">
                      AI
                    </div>

                    <div className="flex flex-1 flex-col gap-3">
                      <div className="rounded-[18px] rounded-bl border border-slate-200 bg-slate-50 px-[18px] py-4">
                        <p className="text-[15px] leading-relaxed">
                          {message.text}
                        </p>

                        {message.evidence && (
                          <p className="mt-2.5 text-xs text-slate-500">
                            {message.evidence}
                          </p>
                        )}
                      </div>

                      {message.sources?.length > 0 && (
                        <>
                          <p className="text-[13px] font-bold text-slate-700">
                            출처 {message.sources.length}개
                          </p>

                          <div className="grid grid-cols-3 gap-3">
                            {message.sources.map((source) => (
                              <SourceCard
                                key={`${source.doc}-${source.page}`}
                                source={source}
                              />
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex items-center gap-3 rounded-[18px] border border-slate-200 bg-slate-50 p-3">
              <div className="flex h-12 flex-1 items-center gap-2.5 rounded-[14px] border border-slate-300 bg-white px-4">
                <span className="font-mono font-extrabold text-blue-600">
                  ?
                </span>

                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={handleEnterKeyDown}
                  className="flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400"
                  placeholder="사내 규정에 대해 질문하세요"
                />
              </div>

              <button
                type="button"
                onClick={handleSendMessage}
                className="h-12 w-28 rounded-[14px] bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700"
              >
                전송
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}