"use client";

interface RouteErrorProps {
  error: Error & {
    digest?: string;
  };
  reset: () => void;
}

export default function RouteError({
  reset,
}: RouteErrorProps) {
  return (
    <main className="route-state">
      <p className="eyebrow">Route unavailable</p>
      <h1>The Control Room could not render this view</h1>
      <p>
        The failure is isolated to this route. Retry without changing
        profile data or navigation state.
      </p>
      <button type="button" onClick={reset}>
        Retry route
      </button>
    </main>
  );
}
