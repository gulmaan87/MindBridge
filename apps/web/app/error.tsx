"use client";

import { useEffect } from "react";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error securely without exposing user personal data
    console.error("Application error boundary caught error:", error.message);
  }, [error]);

  return (
    <div
      role="alert"
      className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center"
    >
      <div className="rounded-2xl border border-destructive/20 bg-destructive/10 p-8 max-w-md">
        <h2 className="text-xl font-bold text-destructive">
          Something went wrong
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          An unexpected error occurred while loading this view. You can safely try again.
        </p>
        <button
          onClick={() => reset()}
          className="mt-6 inline-flex min-h-touch-elder items-center justify-center rounded-xl bg-primary px-6 py-2.5 text-sm font-semibold text-primary-foreground shadow hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          Try Again
        </button>
      </div>
    </div>
  );
}
