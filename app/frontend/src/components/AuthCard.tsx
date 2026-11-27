export function AuthCard({ title, sub, children }: { title: string; sub: string; children: React.ReactNode }) {
  return (
    <main className="grid min-h-screen place-items-center px-4 py-10">
      <div className="w-full max-w-[420px]">
        <div className="mb-6 flex items-center gap-2.5 font-display text-xl font-bold">
          <span className="grid size-9 place-items-center rounded-lg bg-accent font-mono text-sm text-accent-ink">MS</span>
          MinutesStudy
        </div>
        <div className="rounded-2xl border border-line bg-surface p-6">
          <h1 className="text-xl font-semibold">{title}</h1>
          <p className="mb-5 mt-1 text-sm text-muted">{sub}</p>
          {children}
        </div>
      </div>
    </main>
  );
}
