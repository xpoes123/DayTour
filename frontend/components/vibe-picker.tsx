"use client";

export type Vibe =
  | "foodie"
  | "art"
  | "family"
  | "outdoors"
  | "nightlife"
  | "hidden_gems";

const VIBES: { id: Vibe | null; label: string; emoji: string }[] = [
  { id: null, label: "Anything", emoji: "✨" },
  { id: "foodie", label: "Foodie", emoji: "🍜" },
  { id: "art", label: "Art", emoji: "🎨" },
  { id: "family", label: "Family", emoji: "👨‍👩‍👧" },
  { id: "outdoors", label: "Outdoors", emoji: "🌳" },
  { id: "nightlife", label: "Nightlife", emoji: "🍸" },
  { id: "hidden_gems", label: "Hidden gems", emoji: "🔎" },
];

export function VibePicker({
  value,
  onChange,
}: {
  value: Vibe | null;
  onChange: (v: Vibe | null) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {VIBES.map((v) => {
        const active = value === v.id;
        return (
          <button
            key={v.id ?? "any"}
            type="button"
            onClick={() => onChange(v.id)}
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition ${
              active
                ? "border-accent bg-accent text-white shadow-sm"
                : "border-ink/15 bg-white text-ink/75 hover:border-accent/40 hover:bg-accent/5"
            }`}
          >
            <span aria-hidden>{v.emoji}</span>
            <span>{v.label}</span>
          </button>
        );
      })}
    </div>
  );
}
