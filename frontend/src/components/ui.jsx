import { NavLink, useNavigate } from "react-router-dom";

import { isAuthenticated, setAuthenticated } from "../lib/auth";

export function PdfIcon({ size = "md" }) {
  const className =
    size === "lg"
      ? "h-[42px] w-[42px] text-[11px]"
      : "h-9 w-9 text-[10px]";

  return (
    <div
      className={`flex items-center justify-center rounded-[10px] bg-red-100 font-mono font-extrabold text-red-600 ${className}`}
    >
      PDF
    </div>
  );
}

export function StatusBadge({ status }) {
  const tone = status.includes("완료")
    ? "bg-emerald-50 text-emerald-600"
    : status.includes("텍스트")
      ? "bg-amber-50 text-amber-600"
      : status.includes("중")
        ? "bg-blue-50 text-blue-600"
        : "bg-slate-100 text-slate-600";

  return (
    <span
      className={`inline-flex w-fit items-center gap-1.5 rounded-full px-2.5 py-1.5 text-xs font-bold ${tone}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {status}
    </span>
  );
}

export function ActionButton({
  children,
  variant = "outline",
  disabled = false,
  onClick,
}) {
  const styles = {
    outline:
      "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50",
    primary: "bg-blue-600 text-white hover:bg-blue-700",
    danger: "border border-red-200 bg-white text-red-600 hover:bg-red-50",
  };

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`h-[34px] rounded-[10px] px-3 text-xs font-bold transition disabled:cursor-not-allowed disabled:opacity-45 ${styles[variant]}`}
    >
      {children}
    </button>
  );
}

export function PageShell({ children, className = "", direction = "column" }) {
  const directionClass = direction === "row" ? "flex-row" : "flex-col";

  return (
    <div
      className={`mx-auto flex min-h-[calc(100vh-136px)] w-full max-w-[1296px] ${directionClass} gap-6 ${className}`}
    >
      {children}
    </div>
  );
}

export function PageHeader({ title, description, action, children }) {
  return (
    <header className="flex min-h-14 items-center gap-5">
      <div className="min-w-0 flex-1">
        {children}
        <h1 className="text-[34px] font-bold tracking-normal text-slate-950">
          {title}
        </h1>
        {description && (
          <p className="mt-2 text-[15px] leading-relaxed text-slate-500">
            {description}
          </p>
        )}
      </div>

      {action}
    </header>
  );
}

export function Panel({ children, className = "", as: Component = "section" }) {
  return (
    <Component
      className={`rounded-[20px] border border-slate-200 bg-white ${className}`}
    >
      {children}
    </Component>
  );
}

export function AppLayout({ children }) {
  const navigate = useNavigate();
  const authenticated = isAuthenticated();

  const navItems = [
    { to: "/upload", label: "문서 업로드" },
    { to: "/documents", label: "문서 관리" },
    { to: "/chat", label: "챗봇" },
  ];

  const handleLogout = () => {
    setAuthenticated(false);
    navigate("/login");
  };

  return (
    <main className="min-h-screen bg-[#F8FAFC] p-6 font-sans text-slate-950">
      <nav className="mb-8 flex h-14 items-center gap-2.5 rounded-[18px] border border-slate-200 bg-white px-4">
        <NavLink to="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-[10px] bg-blue-600 font-mono text-base font-extrabold text-white">
            Q
          </span>
          <span className="text-base font-extrabold">Intra-Q</span>
        </NavLink>

        <div className="flex-1" />

        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex h-9 items-center rounded-[10px] px-3.5 text-sm font-bold transition ${
                isActive
                  ? "bg-blue-50 text-blue-600"
                  : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}

        {authenticated ? (
          <div className="ml-3 flex h-9 items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-2.5">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-xs font-bold text-white">
              D
            </div>

            <span className="text-sm font-semibold text-slate-700">
              Demo User
            </span>

            <button
              type="button"
              className="text-xs font-semibold text-slate-500 hover:text-blue-600"
            >
              내 정보
            </button>

            <button
              type="button"
              onClick={handleLogout}
              className="text-xs font-semibold text-red-500 hover:text-red-600"
            >
              로그아웃
            </button>
          </div>
        ) : (
          <div className="ml-3 flex items-center gap-2">
            <button
              type="button"
              onClick={() => navigate("/login")}
              className="h-9 rounded-[10px] border border-slate-300 bg-white px-3.5 text-sm font-bold text-slate-700 transition hover:bg-slate-50"
            >
              로그인
            </button>

            <button
              type="button"
              onClick={() => navigate("/signup")}
              className="h-9 rounded-[10px] bg-blue-600 px-3.5 text-sm font-bold text-white transition hover:bg-blue-700"
            >
              회원가입
            </button>
          </div>
        )}
      </nav>

      {children}
    </main>
  );
}
