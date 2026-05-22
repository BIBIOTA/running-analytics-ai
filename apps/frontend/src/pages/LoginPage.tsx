const STRAVA_AUTH_URL = "/api/auth/strava";

export function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#101828] px-6 py-12 text-white">
      <section className="w-full max-w-[420px] rounded-lg border border-white/10 bg-[#172033] p-8 shadow-2xl">
        <div className="mb-8 flex items-center gap-3">
          <img src="/logo.png" alt="Running Analytics AI" className="h-10 w-10 rounded-md" />
          <div>
            <h1 className="text-2xl font-semibold">Running Analytics AI</h1>
            <p className="mt-1 text-sm text-[#98a2b3]">Connect your Strava account to continue.</p>
          </div>
        </div>

        <a
          className="flex h-12 w-full items-center justify-center rounded-md bg-[#fc4c02] px-4 text-sm font-semibold text-white transition hover:bg-[#e34402] focus:outline-none focus:ring-2 focus:ring-[#fc4c02] focus:ring-offset-2 focus:ring-offset-[#172033]"
          href={STRAVA_AUTH_URL}
        >
          Continue with Strava
        </a>
      </section>
    </main>
  );
}
