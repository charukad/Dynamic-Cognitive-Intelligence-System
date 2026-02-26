import Link from "next/link";
import { Brain, Network, Trophy, Activity, GitBranch, Database, Dna, Sparkles, Wrench } from "lucide-react";

const modules = [
  { href: "/multimodal", title: "Multi-modal", desc: "Image and audio analysis workflows", icon: Network },
  { href: "/tournaments", title: "Tournaments", desc: "GAIA match visualization and control", icon: Trophy },
  { href: "/analytics", title: "Analytics", desc: "Performance and systems metrics", icon: Activity },
  { href: "/conductor", title: "Conductor", desc: "Task plans and orchestration graph", icon: GitBranch },
  { href: "/memory", title: "Memory", desc: "Knowledge graph and episodic timeline", icon: Database },
  { href: "/evolution", title: "Evolution", desc: "Agent fitness and generation trends", icon: Dna },
  { href: "/intelligence", title: "Intelligence", desc: "Metacognition and neurosymbolic tools", icon: Sparkles },
  { href: "/operations", title: "Operations", desc: "Runtime health and infrastructure status", icon: Wrench },
];

export default function OverviewPage() {
  return (
    <div className="min-h-full p-6 md:p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        <header className="rounded-2xl border border-white/10 bg-gradient-to-br from-cyan-950/40 via-slate-900/40 to-blue-950/40 p-6 md:p-8">
          <div className="flex items-center gap-3">
            <div className="rounded-xl border border-cyan-500/40 bg-cyan-500/10 p-2">
              <Brain className="h-6 w-6 text-cyan-300" />
            </div>
            <h1 className="text-2xl font-semibold tracking-tight text-white md:text-3xl">Dynamic Cognitive Intelligence System</h1>
          </div>
          <p className="mt-4 max-w-3xl text-sm text-slate-300 md:text-base">
            Unified command interface for orchestration, memory, analytics, and agent operations.
          </p>
        </header>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {modules.map(({ href, title, desc, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="group rounded-xl border border-white/10 bg-slate-950/60 p-5 transition hover:border-cyan-500/40 hover:bg-slate-900/70"
            >
              <Icon className="h-5 w-5 text-cyan-300" />
              <h2 className="mt-3 text-sm font-semibold text-white">{title}</h2>
              <p className="mt-1 text-xs text-slate-400">{desc}</p>
            </Link>
          ))}
        </section>
      </div>
    </div>
  );
}
