export default function Dashboard() {
  return (
    <main className="min-h-screen bg-[#06111f] px-6 py-8 text-slate-100">
      <section className="mx-auto max-w-6xl">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center border border-cyan-300/60 bg-cyan-300 text-sm font-black text-[#06111f]">
            C
          </div>
          <div>
            <p className="text-lg font-semibold uppercase">clavis</p>
            <p className="text-xs uppercase text-cyan-200/70">Recon Surface</p>
          </div>
        </div>

        <div className="border border-white/10 bg-[#0a1f35] p-6">
          <p className="mb-3 text-sm font-semibold uppercase text-cyan-200">Dashboard</p>
          <h1 className="text-3xl font-semibold text-white">Ambiente autenticado</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
            Proxima etapa: conectar projetos, targets, scans e resultados reais da API.
          </p>
        </div>
      </section>
    </main>
  );
}
