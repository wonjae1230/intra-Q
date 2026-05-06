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

function ServerErrorIcon() {
  return (
    <div className="flex h-[76px] w-[76px] items-center justify-center rounded-full border border-red-200 bg-red-50 font-mono text-[30px] font-extrabold text-red-500">
      !
    </div>
  );
}

function TipsBox({ tips }) {
  return (
    <div className="flex w-full flex-col gap-2.5 rounded-[18px] border border-slate-200 bg-slate-50 p-4 text-sm font-bold text-slate-700">
      {tips.map((tip) => (
        <div key={tip} className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-600" />
          <p>{tip}</p>
        </div>
      ))}
    </div>
  );
}

export default function ErrorStateCard({
  type,
  title,
  description,
  tips,
  primaryAction,
  secondaryAction,
  onPrimaryClick,
  onSecondaryClick,
}) {
  return (
    <article className="mx-auto flex w-full max-w-[620px] flex-col items-center gap-5 rounded-[28px] border border-slate-200 bg-white p-8 text-center shadow-sm">
      {type === "not-found" ? <EmptyDocumentIcon /> : <ServerErrorIcon />}

      <h1 className="text-2xl font-bold tracking-normal text-slate-950">
        {title}
      </h1>

      <p className="max-w-md text-sm leading-relaxed text-slate-500">
        {description}
      </p>

      <TipsBox tips={tips} />

      <div className="flex items-center gap-2.5">
        <button
          type="button"
          onClick={onPrimaryClick}
          className="h-11 rounded-xl bg-blue-600 px-4 text-sm font-bold text-white transition hover:bg-blue-700"
        >
          {primaryAction}
        </button>

        <button
          type="button"
          onClick={onSecondaryClick}
          className="h-11 rounded-xl border border-slate-300 bg-white px-4 text-sm font-bold text-slate-700 transition hover:bg-slate-50"
        >
          {secondaryAction}
        </button>
      </div>
    </article>
  );
}