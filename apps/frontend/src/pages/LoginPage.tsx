const STRAVA_AUTH_URL = "/api/auth/strava";

export function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#0c0e14] px-6 py-12">
      <section className="w-full max-w-[420px] rounded-2xl bg-[#181e2e] px-12 py-10 shadow-2xl">
        <div className="flex flex-col items-center text-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-white p-2">
            <img src="/logo.png" alt="Running Analytics AI" className="h-full w-full object-contain" />
          </div>
          <h1 className="mt-5 text-2xl font-bold text-white">Running Analytics AI</h1>
          <p className="mt-3 text-sm leading-relaxed text-[#8b93a5]">
            連結你的 Strava，用 AI 深度分析每次跑步表現
          </p>
        </div>

        <div className="mt-12">
          <a
            className="flex h-12 w-full items-center justify-center rounded-xl bg-[#fc4c02] text-sm font-bold text-white transition hover:bg-[#e34402] focus:outline-none focus:ring-2 focus:ring-[#fc4c02] focus:ring-offset-2 focus:ring-offset-[#181e2e]"
            href={STRAVA_AUTH_URL}
          >
            使用 Strava 登入
          </a>
        </div>

        <p className="mt-5 text-center text-xs text-[#4b5563]">登入即表示同意我們的服務條款與隱私政策</p>
      </section>
    </main>
  );
}
