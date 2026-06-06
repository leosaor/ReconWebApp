export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#06111f] px-6 py-10 text-slate-100">
      <section className="w-full max-w-md border border-white/10 bg-[#0a1f35] p-6 shadow-2xl shadow-black/20">
        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center border border-cyan-300/60 bg-cyan-300 text-sm font-black text-[#06111f]">
            C
          </div>
          <div>
            <p className="text-lg font-semibold uppercase">clavis</p>
            <p className="text-xs uppercase text-cyan-200/70">Recon Surface</p>
          </div>
        </div>

        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-white">Entrar na plataforma</h1>
          <p className="mt-2 text-sm leading-6 text-slate-400">
            Acesso restrito para usuarios autorizados.
          </p>
        </div>

        <form className="grid gap-5">
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-slate-200">Usuario</span>
            <input
              className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
              name="username"
              placeholder="Digite seu usuario"
              type="text"
            />
          </label>

          <label className="grid gap-2 text-sm">
            <span className="font-medium text-slate-200">Senha</span>
            <input
              className="h-11 border border-white/10 bg-[#06111f] px-3 text-slate-100 outline-none transition focus:border-cyan-300"
              name="password"
              placeholder="Digite sua senha"
              type="password"
            />
          </label>

          <div className="text-sm">
            <label className="flex items-center gap-2 text-slate-300">
              <input className="h-4 w-4 accent-cyan-300" type="checkbox" />
              Manter conectado
            </label>
          </div>

          <button
            className="h-11 border border-cyan-300 bg-cyan-300 px-4 text-sm font-semibold text-[#06111f]"
            type="submit"
          >
            Entrar
          </button>
        </form>
      </section>
    </main>
  );
}
