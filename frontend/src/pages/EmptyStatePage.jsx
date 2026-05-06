import { useNavigate } from "react-router-dom";

const steps = [
  {
    number: "1",
    title: "PDF 문서 업로드",
    description: "사내 규정과 가이드를 추가합니다.",
  },
  {
    number: "2",
    title: "문서 자동 분석",
    description: "텍스트 추출, 청크 분할, 임베딩을 생성합니다.",
  },
  {
    number: "3",
    title: "질문하고 출처와 함께 답변 받기",
    description: "AI 답변과 근거 문단을 함께 확인합니다.",
  },
];

function Illustration() {
  return (
    <div className="relative h-[220px] w-[360px] rounded-[28px] border border-slate-200 bg-slate-50 shadow-sm">
      <div className="absolute left-[58px] top-[34px] h-[154px] w-[132px] rounded-2xl border border-slate-300 bg-white">
        <div className="absolute right-0 top-0 h-10 w-10 rounded-bl-xl border border-blue-200 bg-blue-50" />

        <div className="absolute left-[18px] top-5 flex h-6 w-12 items-center justify-center rounded-lg bg-red-100 font-mono text-[11px] font-extrabold text-red-600">
          PDF
        </div>

        <div className="absolute left-[18px] top-[62px] h-2 w-[92px] rounded bg-slate-200" />
        <div className="absolute left-[18px] top-[84px] h-2 w-[74px] rounded bg-slate-200" />
        <div className="absolute left-[18px] top-[106px] h-2 w-24 rounded bg-slate-200" />
      </div>

      <svg
        viewBox="0 0 58 18"
        className="absolute left-[130px] top-[106px] h-[18px] w-[58px]"
      >
        <path
          d="M0 9c18-9 38 9 58 0"
          className="fill-none stroke-blue-600 stroke-[2px]"
          strokeLinecap="round"
        />
      </svg>

      <div className="absolute left-40 top-[68px] flex h-[92px] w-[150px] flex-col gap-2 rounded-[18px] border border-blue-200 bg-blue-50 p-3.5">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 font-mono text-[9px] font-extrabold text-white">
            AI
          </div>
          <span className="font-mono text-[11px] font-bold text-blue-600">
            Q&amp;A Bot
          </span>
        </div>

        <div className="h-[7px] w-full rounded bg-blue-200" />
        <div className="h-[7px] w-[92px] rounded bg-blue-200" />
      </div>
    </div>
  );
}

function StepCard({ number, title, description }) {
  return (
    <article className="flex h-[150px] flex-1 flex-col items-center gap-3 rounded-[20px] border border-slate-200 bg-slate-50 p-[18px] text-center transition hover:border-blue-200 hover:bg-blue-50">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-50 font-mono text-sm font-extrabold text-blue-600">
        {number}
      </div>

      <h3 className="text-[15px] font-bold text-slate-950">{title}</h3>
      <p className="text-[13px] leading-snug text-slate-500">{description}</p>
    </article>
  );
}

export default function EmptyStatePage() {
  const navigate = useNavigate();

  return (
    <main className="min-h-screen bg-white p-6 font-sans text-slate-950">
      <div className="mx-auto flex min-h-[calc(100vh-48px)] max-w-[1000px] flex-col items-center justify-center gap-7">
        <Illustration />

        <section className="text-center">
          <h1 className="text-[42px] font-bold tracking-normal">
            기업 내부 문서 Q&amp;A 봇
          </h1>
          <p className="mt-4 text-lg text-slate-500">
            사내 문서를 업로드하고 AI에게 질문해보세요.
          </p>
        </section>

        <section className="grid w-full grid-cols-3 gap-4">
          {steps.map((step) => (
            <StepCard key={step.number} {...step} />
          ))}
        </section>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate("/upload")}
            className="h-[50px] rounded-[14px] bg-blue-600 px-5 text-[15px] font-bold text-white transition hover:bg-blue-700"
          >
            문서 업로드 시작하기
          </button>

          <button
            type="button"
            onClick={() => navigate("/chat")}
            className="h-[50px] rounded-[14px] border border-slate-300 bg-white px-5 text-[15px] font-bold text-slate-700 transition hover:bg-slate-50"
          >
            샘플 문서로 체험하기
          </button>
        </div>
      </div>
    </main>
  );
}