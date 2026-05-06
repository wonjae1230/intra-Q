import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { pageSources } from "../data/mockData";
import { AppLayout } from "../components/ui";

const documentInfo = {
  name: "인사규정.pdf",
  uploadDate: "2026-05-04",
  pages: "24페이지",
  chunks: "86청크",
};

function MetaPill({ children }) {
  return (
    <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-600">
      {children}
    </span>
  );
}

function PageThumbnail({ page, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex h-[92px] w-full items-center justify-center rounded-[10px] font-mono text-[13px] font-bold transition ${
        active
          ? "border-2 border-blue-600 bg-blue-50 text-blue-600"
          : "border border-slate-200 bg-white text-slate-500 hover:border-blue-200 hover:bg-blue-50"
      }`}
    >
      {page}
    </button>
  );
}

function SourceRow({ label, children }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="w-24 text-[13px] font-bold text-slate-500">
        {label}
      </span>
      <div className="text-sm font-bold text-slate-950">{children}</div>
    </div>
  );
}

export default function DocumentDetailPage() {
  const navigate = useNavigate();
  const [selectedPage, setSelectedPage] = useState("18");

  const selectedSource = useMemo(() => {
    return pageSources.find((source) => source.page === selectedPage);
  }, [selectedPage]);

  const meta = [
    `업로드일 ${documentInfo.uploadDate}`,
    documentInfo.pages,
    documentInfo.chunks,
  ];

  return (
    <AppLayout>
      <div className="mx-auto flex min-h-[calc(100vh-136px)] max-w-[1296px] flex-col gap-[22px]">
        <header className="flex items-center gap-5">
          <div className="flex-1">
            <button
              type="button"
              onClick={() => navigate("/documents")}
              className="mb-3 text-sm font-bold text-slate-500 transition hover:text-blue-600"
            >
              ← 문서 관리로 돌아가기
            </button>

            <h1 className="text-[34px] font-bold tracking-normal">
              문서 상세 보기
            </h1>
            <p className="mt-2 text-base font-bold text-blue-600">
              {documentInfo.name}
            </p>
          </div>

          <div className="flex justify-end gap-2">
            {meta.map((item) => (
              <MetaPill key={item}>{item}</MetaPill>
            ))}
          </div>
        </header>

        <div className="flex flex-1 gap-6">
          <section className="flex flex-1 flex-col gap-3.5 rounded-3xl border border-slate-200 bg-white p-[18px]">
            <div className="flex h-11 items-center gap-2.5">
              <span className="rounded-full bg-blue-50 px-3 py-1.5 font-mono text-xs font-bold text-blue-600">
                Page {selectedSource.page} selected
              </span>

              <div className="flex-1" />

              <span className="rounded-[10px] border border-slate-200 bg-slate-50 px-3 py-1.5 font-mono text-xs font-bold text-slate-600">
                100%
              </span>
            </div>

            <div className="flex flex-1 gap-4 rounded-[18px] bg-slate-100 p-4">
              <aside className="flex w-[72px] flex-col gap-2.5">
                {pageSources.map((item) => (
                  <PageThumbnail
                    key={item.page}
                    page={item.page}
                    active={item.page === selectedPage}
                    onClick={() => setSelectedPage(item.page)}
                  />
                ))}
              </aside>

              <div className="flex flex-1 items-center justify-center">
                <div className="relative h-[640px] w-[610px] rounded-lg border border-slate-300 bg-white shadow-sm">
                  <h2 className="absolute left-[54px] top-12 text-xl font-bold text-slate-900">
                    {selectedSource.title}
                  </h2>

                  <p className="absolute left-[54px] top-[84px] text-sm font-bold text-slate-700">
                    {selectedSource.section}
                  </p>

                  <div className="absolute left-[54px] top-32 h-[9px] w-[500px] rounded bg-slate-200" />
                  <div className="absolute left-[54px] top-[152px] h-[9px] w-[454px] rounded bg-slate-200" />

                  <div className="absolute left-11 top-[198px] flex h-[116px] w-[522px] flex-col gap-2 rounded-xl border-2 border-blue-600 bg-blue-50 p-3.5">
                    <p className="font-mono text-[11px] font-bold text-blue-600">
                      선택된 출처 문단
                    </p>
                    <p className="text-sm leading-relaxed text-slate-950">
                      {selectedSource.highlight}
                    </p>
                  </div>

                  <div className="absolute left-[54px] top-[350px] h-[9px] w-[492px] rounded bg-slate-200" />
                  <div className="absolute left-[54px] top-[374px] h-[9px] w-[420px] rounded bg-slate-200" />
                  <div className="absolute left-[54px] top-[420px] h-[9px] w-[500px] rounded bg-slate-200" />

                  <div className="absolute bottom-8 left-1/2 -translate-x-1/2 font-mono text-xs font-bold text-slate-400">
                    - {selectedSource.page} -
                  </div>
                </div>
              </div>
            </div>
          </section>

          <aside className="flex w-[390px] flex-col gap-4 rounded-3xl border border-slate-200 bg-white p-5">
            <h2 className="text-xl font-bold">출처 정보</h2>

            <section className="rounded-2xl border border-blue-200 bg-blue-50 p-3.5">
              <span className="inline-flex rounded-full bg-white px-2.5 py-1 text-xs font-bold text-blue-600">
                답변에 사용된 출처
              </span>
              <p className="mt-2 text-[15px] font-bold text-slate-950">
                선택한 문단이 AI 답변의 근거로 사용되었습니다.
              </p>
            </section>

            <section className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <SourceRow label="문서명">{documentInfo.name}</SourceRow>

              <SourceRow label="페이지 번호">
                <span className="font-mono">{selectedSource.page}페이지</span>
              </SourceRow>

              <SourceRow label="유사도 점수">
                <span className="rounded-full bg-blue-600 px-2.5 py-1.5 font-mono text-xs font-extrabold text-white">
                  {selectedSource.score}
                </span>
              </SourceRow>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-bold">검색된 청크 본문</h3>
              <p className="mt-2.5 text-sm leading-relaxed text-slate-700">
                {selectedSource.chunk}
              </p>
            </section>

            <section className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
              <h3 className="text-sm font-bold">연결된 답변</h3>
              <p className="mt-2 text-[13px] leading-relaxed text-slate-600">
                {selectedSource.answer}
              </p>
            </section>

            <button
              type="button"
              onClick={() => navigate("/chat")}
              className="mt-auto h-11 rounded-xl bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700"
            >
              이 문서로 질문하기
            </button>
          </aside>
        </div>
      </div>
    </AppLayout>
  );
}