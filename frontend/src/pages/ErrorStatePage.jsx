import { useState } from "react";

const states = [
  {
    type: "empty",
    title: "문서에서 답을 찾을 수 없습니다",
    description:
      "업로드된 문서에서 질문과 충분히 유사한 근거를 찾지 못했습니다. 질문을 조금 더 구체적으로 바꾸거나 관련 문서를 추가해보세요.",
    secondaryAction: "다른 문서 선택",
  },
  {
    type: "error",
    title: "요청 처리 중 오류가 발생했습니다",
    description:
      "일시적인 네트워크 문제나 문서 처리 상태 때문에 답변을 생성하지 못했습니다. 잠시 후 다시 시도하거나 다른 문서를 선택하세요.",
    secondaryAction: "문서 다시 업로드",
  },
];

function EmptyDocumentIcon() {
  return (
    <div className="relative h-[76px] w-[76px] rounded-full border border-amber-200 bg-amber-50">
      <div className="absolute left-[22px] top-[17px] h-[42px] w-8 rounded-md border border-amber-400 bg-white">
        <div className="absolute left-[7px] top-3.5 h-1 w-[18px] rounded bg-amber-400" />
        <div className="absolute left-[7px] top-6 h-1 w-3.5 rounded bg-amber-200" />
      </div>
    </div>
  );
}

function ErrorIcon() {
  return (
    <div className="flex h-[76px] w-[76px] items-center justify-center rounded-full border border-red-200 bg-red-50 font-mono text-[30px] font-extrabold text-red-500">
      !
    </div>
  );
}

function TipsBox() {
  return (
    <div className="flex w-full flex-col gap-2.5 rounded-[18px] border border-slate-200 bg-slate-50 p-4 text-sm font-bold text-slate-700">
      <div className="flex items-center gap-2">
        <span className="h-1.5 w-1.5 rounded-full bg-blue-600" />
        <p>질문 표현을 바꿔보세요</p>
      </div>

      <div className="flex items-center gap-2">
        <span className="h-1.5 w-1.5 rounded-full bg-blue-600" />
        <p>관련 문서가 업로드되어 있는지 확인하세요</p>
      </div>
    </div>
  );
}

function StateCard({ type, title, description, secondaryAction }) {
  const [notice, setNotice] = useState("");

  const handleRetry = () => {
    setNotice("다시 답변 생성을 시도합니다.");
  };

  const handleSecondaryAction = () => {
    if (type === "empty") {
      setNotice("다른 문서를 선택하는 화면으로 이동할 예정입니다.");
      return;
    }

    setNotice("문서 업로드 화면으로 이동할 예정입니다.");
  };

  return (
    <article className="flex h-[500px] flex-1 flex-col items-center gap-5 rounded-[28px] border border-slate-200 bg-white p-8 text-center shadow-sm">
      {type === "empty" ? <EmptyDocumentIcon /> : <ErrorIcon />}

      <h2 className="text-2xl font-bold tracking-normal text-slate-950">
        {title}
      </h2>

      <p className="max-w-md text-sm leading-relaxed text-slate-500">
        {description}
      </p>

      <TipsBox />

      <div className="flex items-center gap-2.5">
        <button
          type="button"
          onClick={handleRetry}
          className="h-11 rounded-xl bg-blue-600 px-4 text-sm font-bold text-white transition hover:bg-blue-700"
        >
          다시 시도
        </button>

        <button
          type="button"
          onClick={handleSecondaryAction}
          className="h-11 rounded-xl border border-slate-300 bg-white px-4 text-sm font-bold text-slate-700 transition hover:bg-slate-50"
        >
          {secondaryAction}
        </button>
      </div>

      {notice && (
        <div className="mt-auto rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-xs font-bold text-blue-600">
          {notice}
        </div>
      )}
    </article>
  );
}

export default function ErrorStatePage() {
  return (
    <main className="min-h-screen bg-[#F8FAFC] p-6 font-sans text-slate-950">
      <div className="mx-auto flex h-[760px] max-w-[1200px] flex-col gap-7 pt-[70px]">
        <header className="flex flex-col items-center gap-2.5 text-center">
          <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-500">
            상태 안내
          </span>

          <h1 className="text-[34px] font-bold tracking-normal">
            답변을 찾지 못했거나 오류가 발생했을 때
          </h1>

          <p className="text-[15px] text-slate-500">
            사용자가 다음 행동을 바로 선택할 수 있도록 부드럽게 안내합니다.
          </p>
        </header>

        <section className="flex gap-5">
          {states.map((state) => (
            <StateCard key={state.type} {...state} />
          ))}
        </section>
      </div>
    </main>
  );
}