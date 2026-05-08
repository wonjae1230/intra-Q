import { useState } from "react";
import { useNavigate } from "react-router-dom";

function IntraQIllustration() {
  return (
    <div className="relative h-[220px] w-[360px] rounded-[28px] border border-slate-200 bg-slate-50">
      <div className="absolute left-[58px] top-[34px] h-[154px] w-[132px] rounded-2xl border border-slate-300 bg-white">
        <div className="absolute left-5 top-5 rounded-md bg-red-100 px-3 py-1 text-[10px] font-bold text-red-500">
          PDF
        </div>
        <div className="absolute left-5 top-[62px] h-2 w-[92px] rounded bg-slate-200" />
        <div className="absolute left-5 top-[84px] h-2 w-[74px] rounded bg-slate-200" />
        <div className="absolute left-5 top-[106px] h-2 w-[96px] rounded bg-slate-200" />
      </div>

      <div className="absolute left-[160px] top-[68px] h-[92px] w-[150px] rounded-[18px] border border-blue-200 bg-blue-50 p-3">
        <div className="mb-3 flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
            Q
          </div>
          <span className="text-xs font-bold text-blue-700">QA Bot</span>
        </div>
        <div className="mb-2 h-[7px] rounded bg-blue-200" />
        <div className="h-[7px] w-[92px] rounded bg-blue-200" />
      </div>

      <div className="absolute left-[130px] top-[106px] h-[2px] w-[58px] bg-blue-500" />
    </div>
  );
}

function AuthHeader({ description }) {
  return (
    <div className="flex flex-col items-center text-center">
      <IntraQIllustration />

      <h1 className="mt-6 text-[56px] font-extrabold leading-none tracking-tight text-slate-900">
        Intra-Q
      </h1>

      <p className="mt-3 text-[19px] font-bold text-blue-600">
        기업 내부 문서 Q&amp;A 봇
      </p>

      <p className="mt-2 text-base text-slate-500">{description}</p>
    </div>
  );
}

export function LoginPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = (event) => {
    event.preventDefault();

    // TODO: 백엔드 로그인 API 연결 예정
    navigate("/");
  };

  return (
    <main className="min-h-screen bg-white px-6 py-9">
      <div className="mx-auto flex max-w-[900px] flex-col items-center">
        <AuthHeader description="사내 문서를 업로드하고 AI에게 질문해보세요." />

        <form
          onSubmit={handleLogin}
          className="mt-8 w-full max-w-[480px] rounded-3xl border border-slate-200 bg-white p-6 shadow-[0_18px_42px_-22px_rgba(15,23,42,0.35)]"
        >
          <p className="text-xs font-extrabold text-blue-600">INTRA-Q</p>

          <h2 className="mt-3 text-[28px] font-bold text-slate-900">로그인</h2>

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
                onChange={(event) => setEmail(event.target.value)}
                placeholder="name@company.com"
                className="h-[38px] w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
              />
            </label>

            <label className="block">
              <span className="mb-1.5 block text-sm font-semibold text-slate-900">
                비밀번호
              </span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="비밀번호를 입력하세요"
                className="h-[38px] w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
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

          <button
            type="submit"
            className="mt-3 h-11 w-full rounded-[14px] bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700"
          >
            로그인
          </button>

          <button
            type="button"
            onClick={() => navigate("/")}
            className="mt-3 h-[42px] w-full rounded-[14px] border border-slate-300 bg-white text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            샘플 계정으로 체험하기
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
      </div>
    </main>
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

  const handleChange = (field, value) => {
    setForm((prevForm) => ({
      ...prevForm,
      [field]: value,
    }));
  };

  const handleSignup = (event) => {
    event.preventDefault();

    // TODO: 백엔드 회원가입 API 연결 예정
    navigate("/login");
  };

  return (
    <main className="min-h-screen bg-white px-6 py-4">
      <div className="mx-auto flex max-w-[900px] flex-col items-center">
        <AuthHeader description="새 계정을 만들고 사내 문서 Q&A를 시작하세요." />

        <form
          onSubmit={handleSignup}
          className="mt-6 w-full max-w-[480px] rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_18px_42px_-22px_rgba(15,23,42,0.35)]"
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
                onChange={(event) => handleChange("email", event.target.value)}
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

          <button
            type="submit"
            className="mt-4 h-[42px] w-full rounded-[14px] bg-blue-600 text-sm font-bold text-white transition hover:bg-blue-700"
          >
            회원가입
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
  );
}