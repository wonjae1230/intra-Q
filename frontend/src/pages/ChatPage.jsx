import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  AppLayout,
  PageShell,
  Panel,
  PdfIcon,
  StatusBadge,
} from "../components/ui";
import { askQuestion, getDocuments } from "../lib/api";

function mapDocumentFromApi(item) {
  return {
    id: item.document_id ?? item.id,
    name: item.file_name ?? item.name ?? "unknown.pdf",
    pages: item.page_count ?? item.pages ?? "-",
    size: item.size ?? "-",
    status: item.status ?? "처리 완료",
  };
}

function mapSourceFromApi(source, index) {
  const score =
    typeof source?.score === "number"
      ? source.score.toFixed(2)
      : typeof source?.distance === "number"
        ? (1 / (1 + source.distance)).toFixed(2)
        : "-";

  return {
    id: `${source?.document || source?.file_name || "source"}-${source?.page || index}-${index}`,
    documentName: source?.file_name || source?.document || "unknown.pdf",
    page: source?.page ?? "-",
    score,
    text: source?.text || source?.preview || source?.content || "",
  };
}

export default function ChatPage() {
  const navigate = useNavigate();
  const messageEndRef = useRef(null);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [isSending, setIsSending] = useState(false);
  const [loadError, setLoadError] = useState("");

  const wait = (ms) =>
    new Promise((resolve) => {
      setTimeout(resolve, ms);
    });

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
        setDocuments([]);
      }
    };

    loadDocuments();
  }, []);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isSending]);

  const activeDocuments = documents.filter(
    (doc) => doc.status === "처리 완료" || doc.status === "완료"
  );

  const handleSendMessage = async () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || isSending) {
      return;
    }

    const userMessage = {
      id: Date.now(),
      type: "user",
      text: trimmedQuestion,
    };

    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setQuestion("");
    setIsSending(true);
    const minLoadingDelay = wait(1200);

    try {
      const response = await askQuestion(
        trimmedQuestion,
        activeDocuments.map((doc) => doc.id)
      );

      await minLoadingDelay;

      const chatData = response?.data ?? response ?? {};
      const sources = Array.isArray(chatData.sources)
        ? chatData.sources.map(mapSourceFromApi)
        : [];

      const firstSource = sources[0];

      setMessages((prevMessages) => [
        ...prevMessages,
        {
          id: Date.now() + 1,
          type: "ai",
          text: chatData.answer || "답변이 비어 있습니다.",
          evidence: firstSource
            ? `근거: ${firstSource.documentName} · p.${firstSource.page}`
            : "",
          sources,
        },
      ]);
    } catch (error) {
      await minLoadingDelay;

      setMessages((prevMessages) => [
        ...prevMessages,
        {
          id: Date.now() + 1,
          type: "ai",
          text: "질문 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
          evidence: error.message,
          sources: [],
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      handleSendMessage();
    }
  };

  return (
    <AppLayout>
      <PageShell direction="row">
        <Panel as="aside" className="flex w-[340px] shrink-0 flex-col gap-5 p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 font-mono text-[22px] font-extrabold text-white">
              Q
            </div>

            <div>
              <h1 className="text-lg font-bold">사내 문서 Q&amp;A</h1>
              <p className="text-[13px] text-slate-500">문서 검색 · 출처 확인</p>
            </div>
          </div>

          <section className="rounded-[18px] border border-slate-200 bg-slate-50 p-4">
            <h2 className="text-[15px] font-bold">문서 추가</h2>

            <button
              type="button"
              onClick={() => navigate("/upload")}
              className="mt-3 flex h-[150px] w-full flex-col items-center justify-center gap-2.5 rounded-2xl border border-blue-200 bg-white transition hover:bg-blue-50"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-blue-50 font-mono text-2xl font-bold text-blue-600">
                ↑
              </div>
              <p className="text-sm font-bold">PDF를 끌어오거나 선택</p>
              <p className="text-xs text-slate-500">
                인사·보안·가이드 문서를 추가하세요
              </p>
            </button>

            <button
              type="button"
              onClick={() => navigate("/upload")}
              className="mt-3 h-10 w-full rounded-xl bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700"
            >
              PDF 추가
            </button>
          </section>

          <section className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <h2 className="text-[15px] font-bold">사용 중인 문서</h2>
              <div className="flex-1" />
              <span className="font-mono text-[13px] font-bold text-slate-500">
                {activeDocuments.length}
              </span>
            </div>

            {activeDocuments.map((doc) => (
              <article
                key={doc.id}
                className="rounded-2xl border border-slate-200 bg-white p-3.5"
              >
                <div className="mb-2.5 flex items-center gap-2.5">
                  <PdfIcon />

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-bold">{doc.name}</p>
                    <p className="text-xs text-slate-500">
                      {doc.pages} pages · {doc.size}
                    </p>
                  </div>
                </div>

                <StatusBadge status={doc.status} />
              </article>
            ))}
          </section>

          <div className="mt-auto rounded-2xl border border-blue-200 bg-blue-50 p-3.5">
            <p className="text-[13px] font-bold text-blue-600">문서가 없나요?</p>
            <p className="mt-1.5 text-xs leading-relaxed text-slate-700">
              PDF를 업로드하면 질문 입력창에서 바로 검색할 수 있습니다.
            </p>
            {loadError && (
              <p className="mt-2 text-xs font-semibold text-red-600">
                문서 목록 로드 실패: {loadError}
              </p>
            )}
          </div>
        </Panel>

        <section className="flex flex-1 flex-col gap-[18px]">
          <header className="flex items-center gap-4 px-0.5 py-1">
            <div className="flex-1">
              <h2 className="text-2xl font-bold">사내 문서 Q&amp;A</h2>
              <p className="text-sm text-slate-500">
                질문하면 관련 문서와 페이지를 함께 보여드립니다.
              </p>
            </div>

            <span className="rounded-full border border-blue-200 bg-blue-50 px-3 py-2 text-[13px] font-semibold text-blue-600">
              {activeDocuments.length}개 문서 사용 중
            </span>
          </header>

          <Panel className="flex min-h-0 flex-1 flex-col gap-[18px] p-6">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-3">
              <p className="text-sm font-bold">현재 대화</p>
              <p className="text-xs text-slate-500">
                처리 완료된 문서에서 답변 근거를 검색합니다.
              </p>
            </div>

            <div className="flex min-h-0 flex-1 flex-col gap-[18px] overflow-y-auto pr-1">
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
                            답변에 사용된 출처
                          </p>

                          <div className="grid grid-cols-3 gap-3">
                            {message.sources.map((source) => (
                              <button
                                key={source.id}
                                type="button"
                                onClick={() => navigate("/documents/detail")}
                                className="rounded-2xl border border-blue-200 bg-white p-3.5 text-left transition hover:bg-blue-50"
                              >
                                <div className="flex items-center gap-2">
                                  <p className="text-[13px] font-bold">
                                    {source.documentName}
                                  </p>
                                  <div className="flex-1" />
                                  <span className="rounded-full bg-blue-50 px-2 py-1 font-mono text-[11px] font-bold text-blue-600">
                                    {source.score}
                                  </span>
                                  <span className="font-mono text-base font-extrabold text-blue-600">
                                    ›
                                  </span>
                                </div>

                                <p className="mt-2.5 font-mono text-xs font-bold text-slate-500">
                                  p. {source.page}
                                </p>
                                <p className="mt-2.5 text-xs leading-relaxed text-slate-600">
                                  {source.text}
                                </p>
                              </button>
                            ))}
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}

              {isSending && (
                <div className="flex gap-3">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-950 font-mono text-[13px] font-extrabold text-white">
                    AI
                  </div>

                  <div className="flex flex-1 flex-col gap-3">
                    <div className="rounded-[18px] rounded-bl border border-slate-200 bg-slate-50 px-[18px] py-4">
                      <p className="text-[15px] leading-relaxed text-slate-700">
                        관련 문서를 찾고 답변을 생성하는 중입니다...
                      </p>
                      <div className="mt-3 flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-blue-500 animate-bounce [animation-delay:0ms]" />
                        <span className="h-2 w-2 rounded-full bg-blue-500 animate-bounce [animation-delay:120ms]" />
                        <span className="h-2 w-2 rounded-full bg-blue-500 animate-bounce [animation-delay:240ms]" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messageEndRef} />
            </div>

            <div className="flex items-center gap-3 rounded-[18px] border border-slate-200 bg-slate-50 p-3">
              <div className="flex h-12 flex-1 items-center gap-2.5 rounded-[14px] border border-slate-300 bg-white px-4">
                <input
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={isSending}
                  className="flex-1 bg-transparent text-sm outline-none placeholder:text-slate-400"
                  placeholder="질문을 입력하세요"
                />
              </div>

              <button
                type="button"
                onClick={handleSendMessage}
                disabled={isSending}
                className="h-12 w-28 rounded-[14px] bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSending ? "생성 중..." : "전송"}
              </button>
            </div>

            <div className="flex justify-end gap-2 text-xs">
              <button
                type="button"
                onClick={() => navigate("/error/not-found")}
                className="font-bold text-slate-400 hover:text-blue-600"
              >
                답변 없음 화면 확인
              </button>
              <span className="text-slate-300">|</span>
              <button
                type="button"
                onClick={() => navigate("/error/server")}
                className="font-bold text-slate-400 hover:text-blue-600"
              >
                서버 오류 화면 확인
              </button>
            </div>
          </Panel>
        </section>
      </PageShell>
    </AppLayout>
  );
}
