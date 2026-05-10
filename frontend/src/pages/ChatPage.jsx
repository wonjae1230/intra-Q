import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import ReactMarkdown from "react-markdown";

import {
  AppLayout,
  PageShell,
  Panel,
  PdfIcon,
  StatusBadge,
} from "../components/ui";
import {
  askQuestion,
  clarifyQuestion,
  createChatSession,
  deleteChatSession,
  getChatSessionMessages,
  getChatSessions,
  getDocuments,
  updateChatSession,
} from "../lib/api";

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

function mapChatMessageFromApi(message) {
  const role = message?.role === "assistant" ? "ai" : message?.role;

  return {
    id: `history-${message.id}`,
    type: role === "system" ? "ai" : role,
    text: message?.content ?? "",
    evidence: "",
    sources: [],
    createdAt: message?.created_at ?? null,
  };
}

function mapSessionFromApi(session) {
  return {
    id: session.session_id,
    title: session.title || "새 채팅",
    updatedAt: session.updated_at,
    messageCount: session.message_count ?? 0,
    lastMessage: session.last_message || "",
  };
}

function ContextRequestMessage({ message, onSubmitContext, disabled }) {
  const [contextInput, setContextInput] = useState("");

  const handleSubmit = () => {
    if (!contextInput.trim() || disabled) return;
    onSubmitContext(message.id, message.originalQuestion, contextInput.trim());
  };

  return (
    <div className="flex gap-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-950 font-mono text-[13px] font-extrabold text-white">
        AI
      </div>

      <div className="flex flex-1 flex-col gap-3">
        <div className="rounded-[18px] rounded-bl border border-slate-200 bg-slate-50 px-[18px] py-4">
          <p className="text-[15px] leading-relaxed">{message.contextQuestion}</p>
        </div>

        {!message.answered && (
          <div className="flex gap-2">
            <input
              type="text"
              value={contextInput}
              onChange={(e) => setContextInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
              disabled={disabled}
              placeholder="예: 소프트웨어융합학과 3학년"
              className="flex-1 rounded-[14px] border border-slate-300 bg-white px-4 py-2.5 text-sm outline-none focus:border-blue-400 disabled:opacity-60 placeholder:text-slate-400"
            />
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!contextInput.trim() || disabled}
              className="h-10 rounded-[14px] bg-blue-600 px-4 text-sm font-bold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              확인
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function ClarifyMessage({ message, onSelectOption, onSubmit, disabled }) {
  const hasSelection = message.selectedId !== null;

  return (
    <div className="flex gap-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-950 font-mono text-[13px] font-extrabold text-white">
        AI
      </div>

      <div className="flex flex-1 flex-col gap-3">
        <div className="rounded-[18px] rounded-bl border border-slate-200 bg-slate-50 px-[18px] py-4">
          <p className="text-[15px] leading-relaxed">
            질문을 분석했습니다. 어떤 방향으로 답변할까요?
          </p>
          <p className="mt-1 text-xs text-slate-500">하나를 선택하면 그 관점에 맞게 답변드립니다.</p>
        </div>

        <div className="flex flex-col gap-2">
          {message.options.map((opt) => {
            const isSelected = message.selectedId === opt.id;
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => !message.answered && onSelectOption(message.id, opt.id)}
                disabled={message.answered || disabled}
                className={`rounded-2xl border p-3.5 text-left transition ${
                  isSelected
                    ? "border-blue-500 bg-blue-50 ring-2 ring-blue-200"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                } disabled:cursor-not-allowed disabled:opacity-60`}
              >
                <div className="flex items-center gap-2">
                  <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition ${isSelected ? "border-blue-500 bg-blue-500" : "border-slate-300"}`}>
                    {isSelected && <span className="h-2 w-2 rounded-full bg-white" />}
                  </span>
                  <p className="text-[14px] font-bold leading-snug">{opt.label}</p>
                </div>
                {opt.description && (
                  <p className="mt-1.5 pl-7 text-xs leading-relaxed text-slate-500">
                    {opt.description}
                  </p>
                )}
              </button>
            );
          })}
        </div>

        {!message.answered && (
          <button
            type="button"
            onClick={() => onSubmit(message.id, message.question, message.selectedId, message.documentIds)}
            disabled={!hasSelection || disabled}
            className="h-10 w-full rounded-[14px] bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {hasSelection ? "이 방향으로 답변받기" : "방향을 선택하세요"}
          </button>
        )}
      </div>
    </div>
  );
}

export default function ChatPage() {
  const navigate = useNavigate();
  const messageListRef = useRef(null);

  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [chatSessions, setChatSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [chatView, setChatView] = useState("list");
  const [documents, setDocuments] = useState([]);
  const [isSending, setIsSending] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [sessionDocumentIds, setSessionDocumentIds] = useState(null);

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

  const refreshChatSessions = async () => {
    const response = await getChatSessions();
    const rows = response?.data ?? [];
    if (!Array.isArray(rows)) {
      throw new Error("채팅 세션 목록 응답 형식이 올바르지 않습니다.");
    }
    const mappedSessions = rows.map(mapSessionFromApi);
    setChatSessions(mappedSessions);
    return mappedSessions;
  };

  const loadSessionMessages = async (sessionId) => {
    const response = await getChatSessionMessages(sessionId, { limit: 50, order: "asc" });
    const rows = response?.data ?? [];
    if (!Array.isArray(rows)) {
      throw new Error("채팅 메시지 응답 형식이 올바르지 않습니다.");
    }
    setMessages(rows.map(mapChatMessageFromApi));
  };

  const openChatSession = async (sessionId) => {
    setActiveSessionId(sessionId);
    setMessages([]);
    setSessionDocumentIds(null);
    await loadSessionMessages(sessionId);
    setChatView("room");
  };

  const handleOpenChatSession = async (sessionId) => {
    if (isSending) return;
    try {
      setLoadError("");
      await openChatSession(sessionId);
    } catch (error) {
      setLoadError(error.message);
    }
  };

  const ensureActiveSession = async (title = null) => {
    if (activeSessionId) {
      return activeSessionId;
    }

    const response = await createChatSession(title);
    const created = response?.data;
    if (!created?.session_id) {
      throw new Error("채팅 세션 생성 응답 형식이 올바르지 않습니다.");
    }

    const newSession = {
      id: created.session_id,
      title: created.title || "새 채팅",
      updatedAt: created.created_at,
      messageCount: 0,
      lastMessage: "",
    };
    setChatSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(created.session_id);
    setMessages([]);
    setSessionDocumentIds(null);
    return created.session_id;
  };

  useEffect(() => {
    let isActive = true;

    const loadChatSessions = async () => {
      try {
        setIsLoadingSessions(true);
        const sessions = await refreshChatSessions();
        if (!isActive) return;

        if (sessions.length > 0) {
          setActiveSessionId(sessions[0].id);
          setMessages([]);
          setChatView("list");
        } else {
          const response = await createChatSession();
          const created = response?.data;
          if (!created?.session_id) {
            throw new Error("채팅 세션 생성 응답 형식이 올바르지 않습니다.");
          }
          if (!isActive) return;
          setChatSessions([
            {
              id: created.session_id,
              title: created.title || "새 채팅",
              updatedAt: created.created_at,
              messageCount: 0,
              lastMessage: "",
            },
          ]);
          setActiveSessionId(created.session_id);
          setMessages([]);
          setChatView("list");
        }
      } catch (error) {
        if (isActive) {
          setLoadError(error.message);
        }
      } finally {
        if (isActive) {
          setIsLoadingSessions(false);
        }
      }
    };

    loadChatSessions();

    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    const messageList = messageListRef.current;
    if (!messageList) return;

    messageList.scrollTo({
      top: messageList.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isSending]);

  const activeDocuments = documents.filter(
    (doc) => doc.status === "처리 완료" || doc.status === "완료"
  );

  const handleSendMessage = async () => {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isSending) return;

    let currentSessionId;
    try {
      currentSessionId = await ensureActiveSession(trimmedQuestion.slice(0, 100));
    } catch (error) {
      setLoadError(error.message);
      return;
    }

    const userMessage = { id: Date.now(), type: "user", text: trimmedQuestion };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setIsSending(true);

    // 이미 문서가 선택된 대화 세션이면 clarify 없이 바로 답변
    if (sessionDocumentIds !== null) {
      await _fetchAnswer(trimmedQuestion, sessionDocumentIds, null, currentSessionId);
      return;
    }

    try {
      const response = await clarifyQuestion(
        trimmedQuestion,
        activeDocuments.map((doc) => doc.id)
      );

      const clarifyData = response?.data ?? {};
      const options = clarifyData.options ?? [];
      const returnedDocumentIds = clarifyData.document_ids ?? activeDocuments.map((doc) => doc.id);
      const contextQuestion = clarifyData.context_question ?? null;

      // AI needs more context from the user
      if (contextQuestion) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            type: "context_request",
            originalQuestion: trimmedQuestion,
            contextQuestion,
            documentIds: returnedDocumentIds,
            answered: false,
          },
        ]);
        setIsSending(false);
        return;
      }

      // LLM decided the question is simple — skip clarify and answer directly
      if (options.length === 0) {
        setSessionDocumentIds(returnedDocumentIds);
        await _fetchAnswer(trimmedQuestion, returnedDocumentIds, null, currentSessionId);
        return;
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          type: "clarify",
          question: trimmedQuestion,
          options,
          selectedId: null,
          documentIds: returnedDocumentIds,
          answered: false,
        },
      ]);
      setIsSending(false);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          type: "ai",
          text: "질문 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
          evidence: error.message,
          sources: [],
        },
      ]);
      setIsSending(false);
    }
  };

  const _fetchAnswer = async (q, documentIds, approachHint = null, sessionId = activeSessionId) => {
    const minLoadingDelay = wait(1200);
    try {
      if (!sessionId) {
        throw new Error("활성 채팅 세션이 없습니다.");
      }
      const response = await askQuestion(sessionId, q, documentIds, approachHint);
      await minLoadingDelay;

      const chatData = response?.data ?? response ?? {};
      const sources = Array.isArray(chatData.sources)
        ? chatData.sources.map(mapSourceFromApi)
        : [];
      const firstSource = sources[0];

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          type: "ai",
          text: chatData.answer || "답변이 비어 있습니다.",
          evidence: firstSource ? `근거: ${firstSource.documentName} · p.${firstSource.page}` : "",
          sources,
        },
      ]);
      await refreshChatSessions();
    } catch (error) {
      await minLoadingDelay;
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          type: "ai",
          text: "답변 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
          evidence: error.message,
          sources: [],
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleSubmitContext = async (messageId, originalQuestion, userContext) => {
    if (isSending) return;
    let currentSessionId;
    try {
      currentSessionId = await ensureActiveSession(originalQuestion.slice(0, 100));
    } catch (error) {
      setLoadError(error.message);
      return;
    }

    setMessages((prev) =>
      prev.map((m) => (m.id === messageId ? { ...m, answered: true } : m))
    );
    // Enrich the original question with user-provided context and restart the flow
    const enrichedQuestion = `${originalQuestion} (${userContext})`;
    const userMsg = { id: Date.now(), type: "user", text: userContext };
    setMessages((prev) => [...prev, userMsg]);
    setIsSending(true);

    try {
      const response = await clarifyQuestion(
        enrichedQuestion,
        activeDocuments.map((doc) => doc.id)
      );
      const clarifyData = response?.data ?? {};
      const options = clarifyData.options ?? [];
      const returnedDocumentIds = clarifyData.document_ids ?? activeDocuments.map((doc) => doc.id);
      const contextQuestion = clarifyData.context_question ?? null;

      if (contextQuestion) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            type: "context_request",
            originalQuestion: enrichedQuestion,
            contextQuestion,
            documentIds: returnedDocumentIds,
            answered: false,
          },
        ]);
        setIsSending(false);
        return;
      }

      if (options.length === 0) {
        setSessionDocumentIds(returnedDocumentIds);
        await _fetchAnswer(enrichedQuestion, returnedDocumentIds, null, currentSessionId);
        return;
      }

      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          type: "clarify",
          question: enrichedQuestion,
          options,
          selectedId: null,
          documentIds: returnedDocumentIds,
          answered: false,
        },
      ]);
      setIsSending(false);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          type: "ai",
          text: "질문 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
          evidence: error.message,
          sources: [],
        },
      ]);
      setIsSending(false);
    }
  };

  const handleSelectOption = (messageId, optionId) => {
    setMessages((prev) =>
      prev.map((msg) => (msg.id === messageId ? { ...msg, selectedId: optionId } : msg))
    );
  };

  const handleSubmitClarify = async (messageId, originalQuestion, selectedId, documentIds) => {
    if (!selectedId || isSending) return;
    const currentSessionId = activeSessionId;
    if (!currentSessionId) {
      setLoadError("활성 채팅 세션이 없습니다.");
      return;
    }

    const msg = messages.find((m) => m.id === messageId);
    const selectedOption = msg?.options.find((o) => o.id === selectedId);
    const approachHint = selectedOption ? `${selectedOption.label}: ${selectedOption.description}` : null;

    setMessages((prev) =>
      prev.map((m) => (m.id === messageId ? { ...m, answered: true } : m))
    );
    setSessionDocumentIds(documentIds);
    setIsSending(true);
    await _fetchAnswer(originalQuestion, documentIds, approachHint, currentSessionId);
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter") {
      handleSendMessage();
    }
  };

  const handleStartNewSession = async () => {
    if (isSending) return;
    try {
      setLoadError("");
      const response = await createChatSession();
      const created = response?.data;
      if (!created?.session_id) {
        throw new Error("채팅 세션 생성 응답 형식이 올바르지 않습니다.");
      }
      setChatSessions((prev) => [
        {
          id: created.session_id,
          title: created.title || "새 채팅",
          updatedAt: created.created_at,
          messageCount: 0,
          lastMessage: "",
        },
        ...prev,
      ]);
      setActiveSessionId(created.session_id);
      setMessages([]);
      setQuestion("");
      setSessionDocumentIds(null);
      setChatView("room");
    } catch (error) {
      setLoadError(error.message);
    }
  };

  const handleRenameSession = async (sessionId) => {
    const current = chatSessions.find((session) => session.id === sessionId);
    const nextTitle = window.prompt("채팅 제목", current?.title || "새 채팅");
    if (nextTitle === null) return;

    try {
      const response = await updateChatSession(sessionId, nextTitle);
      const updated = response?.data;
      setChatSessions((prev) =>
        prev.map((session) =>
          session.id === sessionId
            ? { ...session, title: updated?.title || nextTitle.trim() }
            : session
        )
      );
    } catch (error) {
      setLoadError(error.message);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (isSending || !window.confirm("이 채팅 세션을 삭제할까요?")) return;

    try {
      await deleteChatSession(sessionId);
      const remaining = chatSessions.filter((session) => session.id !== sessionId);
      setChatSessions(remaining);

      if (activeSessionId === sessionId) {
        if (remaining.length > 0) {
          await openChatSession(remaining[0].id);
        } else {
          setActiveSessionId(null);
          setMessages([]);
          setChatView("list");
          await handleStartNewSession();
        }
      }
    } catch (error) {
      setLoadError(error.message);
    }
  };

  return (
    <AppLayout>
      <PageShell direction="row">
        <Panel as="aside" className="flex h-[887.61px] w-[340px] shrink-0 flex-col gap-5 overflow-hidden p-5">
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

          <section className="flex min-h-0 flex-1 flex-col gap-3">
            <div className="flex items-center gap-2">
              <h2 className="text-[15px] font-bold">사용 중인 문서</h2>
              <div className="flex-1" />
              <span className="font-mono text-[13px] font-bold text-slate-500">
                {activeDocuments.length}
              </span>
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain pr-1">
              <div className="flex flex-col gap-3">
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
              </div>
            </div>
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

            <button
              type="button"
              onClick={handleStartNewSession}
              disabled={isSending}
              className="h-10 rounded-xl border border-slate-300 bg-white px-4 text-[13px] font-bold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              새 세션에서 질문하기
            </button>
          </header>

          {chatView === "list" ? (
            <Panel className="flex h-[811.61px] min-h-0 flex-col gap-[18px] overflow-hidden p-6">
              <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-3">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-bold">채팅 세션</p>
                  <p className="text-xs text-slate-500">
                    이어서 질문할 채팅방을 선택하세요.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleStartNewSession}
                  disabled={isSending}
                  className="h-9 rounded-xl bg-blue-600 px-4 text-[13px] font-bold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  새 세션
                </button>
              </div>

              <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain pr-1">
                <div className="grid content-start gap-3">
                {isLoadingSessions && (
                  <div className="rounded-2xl border border-slate-200 bg-white p-4 text-sm font-semibold text-slate-500">
                    불러오는 중
                  </div>
                )}

                {!isLoadingSessions &&
                  chatSessions.map((session) => (
                    <article
                      key={session.id}
                      className="rounded-2xl border border-slate-200 bg-white p-4 transition hover:border-blue-300 hover:bg-blue-50"
                    >
                      <button
                        type="button"
                        onClick={() => handleOpenChatSession(session.id)}
                        disabled={isSending}
                        className="block w-full text-left disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        <div className="flex items-center gap-3">
                          <p className="min-w-0 flex-1 truncate text-base font-bold">
                            {session.title}
                          </p>
                          <span className="rounded-full bg-slate-100 px-2.5 py-1 font-mono text-xs font-bold text-slate-500">
                            {session.messageCount}
                          </span>
                        </div>
                        <p className="mt-2 line-clamp-2 min-h-8 text-sm leading-relaxed text-slate-500">
                          {session.lastMessage || "아직 메시지가 없습니다."}
                        </p>
                      </button>

                      <div className="mt-3 flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => handleRenameSession(session.id)}
                          className="h-8 rounded-[10px] border border-slate-200 bg-white px-3 text-xs font-bold text-slate-600 transition hover:bg-slate-50"
                        >
                          이름 변경
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteSession(session.id)}
                          className="h-8 rounded-[10px] border border-red-200 bg-white px-3 text-xs font-bold text-red-500 transition hover:bg-red-50"
                        >
                          삭제
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            </Panel>
          ) : (
            <Panel className="flex h-[811.61px] min-h-0 flex-col gap-[18px] p-6">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3.5 py-3">
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setChatView("list")}
                  disabled={isSending}
                  className="h-8 rounded-[10px] border border-slate-300 bg-white px-3 text-xs font-bold text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  목록
                </button>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-bold">
                    {chatSessions.find((session) => session.id === activeSessionId)?.title || "현재 대화"}
                  </p>
                  <p className="text-xs text-slate-500">
                    처리 완료된 문서에서 답변 근거를 검색합니다.
                  </p>
                </div>
              </div>
            </div>

            <div ref={messageListRef} className="flex min-h-0 flex-1 flex-col gap-[18px] overflow-y-auto overscroll-contain pr-1">
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

                if (message.type === "context_request") {
                  return (
                    <ContextRequestMessage
                      key={message.id}
                      message={message}
                      onSubmitContext={handleSubmitContext}
                      disabled={isSending}
                    />
                  );
                }

                if (message.type === "clarify") {
                  return (
                    <ClarifyMessage
                      key={message.id}
                      message={message}
                      onSelectOption={handleSelectOption}
                      onSubmit={handleSubmitClarify}
                      disabled={isSending}
                    />
                  );
                }

                return (
                  <div key={message.id} className="flex gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-950 font-mono text-[13px] font-extrabold text-white">
                      AI
                    </div>

                    <div className="flex flex-1 flex-col gap-3">
                      <div className="rounded-[18px] rounded-bl border border-slate-200 bg-slate-50 px-[18px] py-4">
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown>{message.text}</ReactMarkdown>
                        </div>

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
                                  <p className="truncate text-[13px] font-bold">
                                    {source.documentName}
                                  </p>
                                  <div className="flex-1" />
                                  <span className="shrink-0 rounded-full bg-blue-50 px-2 py-1 font-mono text-[11px] font-bold text-blue-600">
                                    {source.score}
                                  </span>
                                  <span className="font-mono text-base font-extrabold text-blue-600">›</span>
                                </div>
                                <p className="mt-2 font-mono text-xs font-bold text-slate-500">
                                  p. {source.page}
                                </p>
                                <p className="mt-2 line-clamp-5 text-xs leading-relaxed text-slate-600">
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
                        관련 문서를 찾고 있습니다...
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
            </div>

            {sessionDocumentIds !== null && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">
                  대화 세션 진행 중
                </span>
                <button
                  type="button"
                  onClick={() => setSessionDocumentIds(null)}
                  className="text-xs font-semibold text-blue-600 hover:text-blue-700"
                >
                  새 질문 시작
                </button>
              </div>
            )}

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
                {isSending ? "검색 중..." : "전송"}
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
          )}
        </section>
      </PageShell>
    </AppLayout>
  );
}
