import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-8 px-6 py-16">
      <header>
        <h1 className="font-display text-5xl">DayTour</h1>
        <p className="mt-2 text-lg opacity-70">
          Tell us where you are. We'll plot a day worth remembering.
        </p>
      </header>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Link
          href="/plan"
          className="rounded-lg bg-ink px-5 py-3 text-paper hover:opacity-90"
        >
          Plan a day
        </Link>
        <Link
          href="/plan/prompt"
          className="rounded-lg border border-ink px-5 py-3 hover:bg-ink hover:text-paper"
        >
          Describe my vibe →
        </Link>
      </div>
    </main>
  );
}
