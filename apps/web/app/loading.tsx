export default function Loading() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex min-h-[60vh] flex-col items-center justify-center p-6 text-center"
    >
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      <p className="mt-4 text-sm font-medium text-muted-foreground">
        Loading MindBridge...
      </p>
      <span className="sr-only">Loading content</span>
    </div>
  );
}
