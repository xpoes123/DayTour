import Image from "next/image";
import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-10 px-6 py-16 text-center">
      <Image
        src="/daytour.png"
        alt="DayTour"
        width={200}
        height={200}
        priority
        className="drop-shadow-md"
      />
      <header>
        <h1 className="font-display text-5xl tracking-tight">DayTour</h1>
        <p className="mt-3 text-lg text-ink/70">
          Tell us where you are. We&apos;ll plot a day worth remembering.
        </p>
      </header>
      <div className="flex flex-col gap-3 sm:flex-row">
        <Link
          href="/plan"
          className="rounded-lg bg-accent px-6 py-3 font-medium text-white shadow-sm hover:bg-accent-dark"
        >
          Plan a day
        </Link>
        <Link
          href="/plan/prompt"
          className="rounded-lg border border-ink/20 px-6 py-3 font-medium text-ink hover:bg-ink hover:text-paper"
        >
          Describe my vibe →
        </Link>
      </div>
      <Link href="/auth" className="text-sm text-ink/50 hover:text-ink">
        Sign in or create an account
      </Link>
    </main>
  );
}
