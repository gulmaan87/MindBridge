import Link from "next/link";
import { Activity, Brain, ShieldCheck, HeartHandshake, Sparkles } from "lucide-react";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-border bg-background/95 backdrop-blur">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <Brain className="h-6 w-6" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight">MindBridge</span>
              <span className="ml-2 hidden rounded-md bg-secondary px-2 py-0.5 text-xs font-semibold text-muted-foreground sm:inline-block">
                MVP v1.0
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              Frontend Active
            </span>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="container flex-1 py-12 md:py-20">
        <div className="mx-auto max-w-3xl text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-1.5 text-xs font-semibold text-primary">
            <ShieldCheck className="h-4 w-4" />
            AI-Powered Cognitive Engagement & Memory Assistance
          </div>

          <h1 className="mt-6 text-4xl font-extrabold tracking-tight sm:text-5xl md:text-6xl">
            Adaptive Support for{" "}
            <span className="text-primary">Every Mind</span>
          </h1>

          <p className="mt-6 text-lg text-muted-foreground sm:text-xl">
            A unified, safety-controlled platform continuously adapting cognitive games,
            personalized memory reminiscence, and caregiver involvement across three
            tailored experiences.
          </p>

          {/* Positioning Disclaimer (Engineering Rules §2) */}
          <div className="mt-6 rounded-xl border border-border/80 bg-secondary/50 p-3.5 text-xs text-muted-foreground">
            <strong>Positioning Notice:</strong> MindBridge provides cognitive engagement and personalized memory assistance. It does not provide clinical diagnosis or automated medical treatment recommendations.
          </div>
        </div>

        {/* 3 Distinct Experience Pillars (PRD §5) */}
        <div className="mt-16 grid gap-6 sm:grid-cols-3">
          {/* Elder Experience Card */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm transition hover:shadow-md">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-elder/10 text-elder">
              <HeartHandshake className="h-6 w-6" />
            </div>
            <h2 className="mt-4 text-xl font-bold text-foreground">Elder Experience</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              High-contrast typography, large touch targets, low cognitive load, and verified photo reminiscence for older adults.
            </p>
            <div className="mt-4 flex items-center gap-2 text-xs font-medium text-elder">
              <span className="rounded-md bg-elder/10 px-2 py-0.5">WCAG 2.1 AA</span>
              <span className="rounded-md bg-elder/10 px-2 py-0.5">≥48px Targets</span>
            </div>
          </div>

          {/* Child Experience Card */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm transition hover:shadow-md">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-child/10 text-child">
              <Sparkles className="h-6 w-6" />
            </div>
            <h2 className="mt-4 text-xl font-bold text-foreground">Child Experience</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Goal-driven attention and working-memory mission games with structured micro-breaks and controlled gamification.
            </p>
            <div className="mt-4 flex items-center gap-2 text-xs font-medium text-child">
              <span className="rounded-md bg-child/10 px-2 py-0.5">Working Memory</span>
              <span className="rounded-md bg-child/10 px-2 py-0.5">Attention Tasks</span>
            </div>
          </div>

          {/* Caregiver Experience Card */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm transition hover:shadow-md">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-caregiver/10 text-caregiver">
              <Activity className="h-6 w-6" />
            </div>
            <h2 className="mt-4 text-xl font-bold text-foreground">Caregiver Dashboard</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Dependent profiles, session trends, memory provenance verification, and granular safety controls.
            </p>
            <div className="mt-4 flex items-center gap-2 text-xs font-medium text-caregiver">
              <span className="rounded-md bg-caregiver/10 px-2 py-0.5">Relationship Auth</span>
              <span className="rounded-md bg-caregiver/10 px-2 py-0.5">Verification Flow</span>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-6 text-center text-xs text-muted-foreground">
        <div className="container flex flex-col items-center justify-between gap-2 sm:flex-row">
          <span>MindBridge Cognitive Platform &copy; 2026</span>
          <span>Next.js 14 &bull; TypeScript &bull; Tailwind CSS &bull; FastAPI Monolith</span>
        </div>
      </footer>
    </div>
  );
}
