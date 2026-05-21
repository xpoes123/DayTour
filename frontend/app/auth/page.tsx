"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { auth } from "@/lib/api";

function AuthForm() {
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next") || "/plan";

  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      if (mode === "register") {
        await auth.register({ username, email, password });
      }
      await auth.login(username, password);
      router.push(next);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Something went wrong";
      setError(msg.replace(/^\d+\s*/, ""));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col items-center justify-center gap-8 px-6 py-12">
      <Link href="/" aria-label="DayTour home" className="transition hover:opacity-80">
        <Image src="/daytour.png" alt="DayTour" width={96} height={96} priority />
      </Link>
      <div className="w-full rounded-xl border border-ink/10 bg-white p-6 shadow-sm">
        <div className="mb-6 flex gap-1 rounded-lg bg-ink/5 p-1 text-sm">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={`flex-1 rounded-md py-1.5 font-medium ${
              mode === "login" ? "bg-white shadow-sm" : "text-ink/60"
            }`}
          >
            Sign in
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            className={`flex-1 rounded-md py-1.5 font-medium ${
              mode === "register" ? "bg-white shadow-sm" : "text-ink/60"
            }`}
          >
            Create account
          </button>
        </div>

        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-ink/80">Username</span>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              className="field"
              required
              minLength={3}
            />
          </label>

          {mode === "register" && (
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-ink/80">Email</span>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                className="field"
                required
              />
            </label>
          )}

          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-ink/80">Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === "register" ? "new-password" : "current-password"}
              className="field"
              required
              minLength={8}
            />
          </label>

          {error && (
            <div className="rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-900">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-accent px-4 py-2.5 font-medium text-white shadow-sm hover:bg-accent-dark disabled:opacity-50"
          >
            {submitting ? "…" : mode === "register" ? "Create account" : "Sign in"}
          </button>
        </form>
      </div>
    </main>
  );
}

export default function AuthPage() {
  return (
    <Suspense fallback={null}>
      <AuthForm />
    </Suspense>
  );
}
