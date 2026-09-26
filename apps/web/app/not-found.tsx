import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center">
      <div className="max-w-md rounded-2xl border border-border bg-card p-8 shadow-sm">
        <h2 className="text-3xl font-extrabold tracking-tight">404</h2>
        <p className="mt-2 text-lg font-medium text-foreground">Page Not Found</p>
        <p className="mt-1 text-sm text-muted-foreground">
          The activity or screen you are looking for does not exist or has been moved.
        </p>
        <div className="mt-6">
          <Link
            href="/"
            className="inline-flex min-h-touch-elder items-center justify-center rounded-xl bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Return to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
