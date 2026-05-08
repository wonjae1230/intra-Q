import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, register } from "../lib/api";

import { setAuthenticated } from "../lib/auth";

const GITHUB_URL = "https://github.com/wonjae1230/intra-Q";

const PIPELINE_STEPS = [
  { icon: "📄", label: "PDF 업로드", sub: "문서 파싱 · 청크 분할" },
  { icon: "🔢", label: "임베딩", sub: "OpenAI text-embedding-3-small" },
  { icon: "🗄️", label: "벡터 저장", sub: "ChromaDB" },
  { icon: "🎯", label: "리랭킹", sub: "Vertex AI Semantic Ranker" },
  { icon: "✨", label: "답변 생성", sub: "Gemini 2.5 Flash" },
];

const TECH_STACK = [
  {
    label: "FastAPI",
    color: "bg-emerald-50 text-emerald-700 border-emerald-200",
  },
  { label: "SQLite", color: "bg-sky-50 text-sky-700 border-sky-200" },
  {
    label: "ChromaDB",
    color: "bg-violet-50 text-violet-700 border-violet-200",
  },
  { label: "OpenAI", color: "bg-slate-50 text-slate-700 border-slate-200" },
  { label: "Vertex AI", color: "bg-blue-50 text-blue-700 border-blue-200" },
  { label: "Gemini", color: "bg-orange-50 text-orange-700 border-orange-200" },
  { label: "React 19", color: "bg-cyan-50 text-cyan-700 border-cyan-200" },
  { label: "JWT Auth", color: "bg-rose-50 text-rose-700 border-rose-200" },
];

function TopNav() {
  return (
    <nav className="flex items-center justify-between px-8 py-4">
      <div className="flex items-center gap-2.5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 font-mono text-sm font-extrabold text-white">
          Q
        </div>
        <span className="text-[15px] font-bold text-slate-900">Intra-Q</span>
      </div>
      <a
        href={GITHUB_URL}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
      >
        <svg
          viewBox="0 0 24 24"
          className="h-4 w-4 fill-current"
          aria-hidden="true"
        >
          <path d="M12 2C6.477 2 2 6.484 2 12.021c0 4.428 2.865 8.185 6.839 9.504.5.092.682-.217.682-.483 0-.237-.009-.868-.013-1.703-2.782.605-3.369-1.342-3.369-1.342-.454-1.154-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.004.07 1.532 1.032 1.532 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0 1 12 6.844a9.59 9.59 0 0 1 2.504.337c1.909-1.296 2.747-1.026 2.747-1.026.546 1.378.202 2.397.1 2.65.64.7 1.028 1.595 1.028 2.688 0 3.848-2.338 4.695-4.566 4.942.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482C19.138 20.203 22 16.447 22 12.021 22 6.484 17.523 2 12 2z" />
        </svg>
        GitHub
      </a>
    </nav>
  );
}

function ArchitecturePanel() {
  return (
    <div className="flex flex-col justify-center gap-8 px-8 py-6">
      <div>
        <p className="text-xs font-extrabold uppercase tracking-widest text-blue-600">
          INTRA-Q
        </p>
        <h1 className="mt-2 text-[42px] font-extrabold leading-tight tracking-tight text-slate-900">
          기업 내부 문서
          <br />
          Q&amp;A 봇
        </h1>
        <p className="mt-3 text-base leading-relaxed text-slate-500">
          사내 PDF 문서를 업로드하면 AI가 읽고 질문에 답합니다.
          <br />
          RAG 파이프라인 기반으로 출처와 근거를 함께 제공합니다.
        </p>
      </div>

      <div>
        <p className="mb-3 text-[13px] font-bold text-slate-700">
          RAG 파이프라인
        </p>
        <div className="flex flex-wrap items-center gap-1.5">
          {PIPELINE_STEPS.map((step, i) => (
            <div key={step.label} className="flex items-center gap-1.5">
              <div className="rounded-2xl border border-slate-200 bg-white px-3 py-2.5 text-center shadow-sm">
                <p className="text-base leading-none">{step.icon}</p>
                <p className="mt-1 text-[11px] font-bold text-slate-800">
                  {step.label}
                </p>
                <p className="mt-0.5 text-[10px] text-slate-400">{step.sub}</p>
              </div>
              {i < PIPELINE_STEPS.length - 1 && (
                <span className="text-slate-300 font-bold">→</span>
              )}
            </div>
          ))}
        </div>
      </div>

      <div>
        <p className="mb-3 text-[13px] font-bold text-slate-700">기술 스택</p>
        <div className="flex flex-wrap gap-2">
          {TECH_STACK.map((tech) => (
            <span
              key={tech.label}
              className={`rounded-full border px-3 py-1 text-[12px] font-semibold ${tech.color}`}
            >
              {tech.label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function AuthHeader({ description }) {
  return (
    <div className="flex flex-col items-center text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 font-mono text-2xl font-extrabold text-white">
        Q
      </div>
      <h1 className="mt-4 text-[40px] font-extrabold leading-none tracking-tight text-slate-900">
        Intra-Q
      </h1>
      <p className="mt-2 text-[17px] font-bold text-blue-600">
        기업 내부 문서 Q&amp;A 봇
      </p>
      <p className="mt-1.5 text-sm text-slate-500">{description}</p>
    </div>
  );
}

export function LoginPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      setAuthenticated(true);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <TopNav />

      <div className="mx-auto flex w-full max-w-[1120px] flex-1 items-center gap-12 px-6 py-8">
        <div className="hidden flex-1 lg:block">
          <ArchitecturePanel />
        </div>

        <div className="mx-auto w-full max-w-[420px] shrink-0">
          <form
            onSubmit={handleLogin}
            className="rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_42px_-22px_rgba(15,23,42,0.35)]"
          >
            <p className="text-xs font-extrabold text-blue-600">INTRA-Q</p>
            <h2 className="mt-3 text-[28px] font-bold text-slate-900">
              로그인
            </h2>
            <p className="mt-2 text-sm text-slate-500">
              업무용 계정으로 로그인하세요.
            </p>

            <div className="mt-5 space-y-4">
              <label className="block">
                <span className="mb-1.5 block text-sm font-semibold text-slate-900">
                  이메일
                </span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="h-[38px] w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
              </label>
              <label className="block">
                <span className="mb-1.5 block text-sm font-semibold text-slate-900">
                  비밀번호
                </span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="비밀번호를 입력하세요"
                  className="h-[38px] w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 text-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
              </label>
            </div>

            <div className="mt-3 flex justify-end">
              <button
                type="button"
                className="text-sm font-semibold text-blue-600 hover:text-blue-700"
              >
                비밀번호 찾기
              </button>
            </div>

            {error && <p className="mt-3 text-sm text-red-500">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="mt-3 h-11 w-full rounded-[14px] bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700 disabled:opacity-60"
            >
              {loading ? "로그인 중..." : "로그인"}
            </button>

            <div className="mt-4 flex items-center justify-center gap-1.5 text-xs">
              <span className="text-slate-500">계정이 없나요?</span>
              <button
                type="button"
                onClick={() => navigate("/signup")}
                className="font-bold text-blue-600 hover:text-blue-700"
              >
                회원가입
              </button>
            </div>
          </form>

          <p className="mt-4 text-center text-xs text-slate-400">
            프로젝트 repo ·{" "}
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-500 hover:underline"
            >
              GitHub
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}

export function SignupPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
    company: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (field, value) => {
    setForm((prevForm) => ({
      ...prevForm,
      [field]: value,
    }));
  };

  const handleSignup = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form.email, form.password, form.name);
      navigate("/login");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <TopNav />
      <main className="flex flex-1 items-center justify-center px-6 py-6">
        <div className="w-full max-w-[480px]">
          <AuthHeader description="새 계정을 만들고 사내 문서 Q&A를 시작하세요." />

          <form
            onSubmit={handleSignup}
            className="mt-6 w-full rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_18px_42px_-22px_rgba(15,23,42,0.35)]"
          >
            <p className="text-xs font-extrabold text-blue-600">INTRA-Q</p>

            <h2 className="mt-2 text-[26px] font-bold text-slate-900">
              회원가입
            </h2>

            <p className="mt-1.5 text-xs text-slate-500">
              서비스 이용을 위한 계정을 생성하세요.
            </p>

            <div className="mt-4 space-y-3">
              <label className="block">
                <span className="mb-1.5 block text-[13px] font-semibold text-slate-900">
                  이름
                </span>
                <input
                  type="text"
                  value={form.name}
                  onChange={(event) => handleChange("name", event.target.value)}
                  placeholder="이름을 입력하세요"
                  className="h-[34px] w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
              </label>

              <label className="block">
                <span className="mb-1.5 block text-[13px] font-semibold text-slate-900">
                  회사명
                </span>
                <input
                  type="text"
                  value={form.company}
                  onChange={(event) =>
                    handleChange("company", event.target.value)
                  }
                  placeholder="회사명을 입력하세요"
                  className="h-[34px] w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
              </label>

              <label className="block">
                <span className="mb-1.5 block text-[13px] font-semibold text-slate-900">
                  이메일
                </span>
                <input
                  type="email"
                  value={form.email}
                  onChange={(event) =>
                    handleChange("email", event.target.value)
                  }
                  placeholder="name@company.com"
                  className="h-[34px] w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
              </label>

              <label className="block">
                <span className="mb-1.5 block text-[13px] font-semibold text-slate-900">
                  비밀번호
                </span>
                <input
                  type="password"
                  value={form.password}
                  onChange={(event) =>
                    handleChange("password", event.target.value)
                  }
                  placeholder="비밀번호를 입력하세요"
                  className="h-[34px] w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
                />
              </label>
            </div>

            {error && <p className="mt-3 text-sm text-red-500">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="mt-4 h-[42px] w-full rounded-[14px] bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700 disabled:opacity-60"
            >
              {loading ? "가입 중..." : "회원가입"}
            </button>

            <div className="mt-3 flex items-center justify-center gap-1.5 text-xs">
              <span className="text-slate-500">이미 계정이 있나요?</span>
              <button
                type="button"
                onClick={() => navigate("/login")}
                className="font-bold text-blue-600 hover:text-blue-700"
              >
                로그인
              </button>
            </div>

            <p className="mt-3 text-center text-[11px] leading-relaxed text-slate-400">
              가입 후 관리자의 승인에 따라 서비스를 이용할 수 있습니다.
            </p>
          </form>
        </div>
      </main>
    </div>
  );
}
