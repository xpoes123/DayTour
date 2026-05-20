"use client";

import Image from "next/image";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, type Itinerary } from "@/lib/api";

const EXAMPLES = [
  "A chill walking day in Madison, Wisconsin — about 4 stops, museums and lakefront",
  "Rainy Saturday in Seattle, mostly indoor places, transit between them",
  "Lower Manhattan tourist loop on foot, 5 stops, hit the financial district highlights",
  "Bicycling day around Boulder, Colorado — outdoorsy, big radius",
];

export default function PromptPlanPage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(text: string) {
    setSubmitting(true);
    setError(null);
    try {
      const itin = await api.post<Itinerary>("/itineraries/from-prompt", {
        prompt: text,
      });
      router.push(`/itinerary/${itin.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not interpret that prompt.");
      setSubmitting(false);
    }
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim()) return;
    submit(prompt.trim());
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <header className="mb-8 flex items-center gap-4">
        <Image src="/daytour.png" alt="" width={56} height={56} />
        <div>
          <h1 className="font-display text-3xl tracking-tight">Describe your day</h1>
          <p className="text-sm text-ink/60">
            We&apos;ll turn it into a plan. The more specific, the better.
          </p>
        </div>
      </header>

      <form onSubmit={onSubmit} className="flex flex-col gap-4">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="A chill walking day in Madison with 4 stops focused on art and the lakefront"
          rows={4}
          required
          minLength={6}
          className="field text-base leading-relaxed"
          disabled={submitting}
        />

        {error && (
          <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={submitting || prompt.trim().length < 6}
          className="self-start rounded-md bg-accent px-5 py-2.5 font-medium text-white shadow-sm hover:bg-accent-dark disabled:opacity-50"
        >
          {submitting ? "Translating into a plan…" : "Build my day →"}
        </button>
      </form>

      <section className="mt-10">
        <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink/50">
          Try one of these
        </div>
        <ul className="flex flex-col gap-2">
          {EXAMPLES.map((ex) => (
            <li key={ex}>
              <button
                type="button"
                onClick={() => {
                  setPrompt(ex);
                  submit(ex);
                }}
                disabled={submitting}
                className="w-full rounded-md border border-ink/10 bg-white px-3 py-2 text-left text-sm text-ink/80 transition hover:border-accent/40 hover:bg-accent/[0.04] disabled:opacity-50"
              >
                {ex}
              </button>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
