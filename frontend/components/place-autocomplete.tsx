"use client";

import { useEffect, useId, useRef, useState } from "react";
import { api, type PlaceSuggestion } from "@/lib/api";

type Props = {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
};

export function PlaceAutocomplete({ value, onChange, placeholder, required }: Props) {
  const listId = useId();
  const [suggestions, setSuggestions] = useState<PlaceSuggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const lastQueryRef = useRef<string>("");
  const lastPickedRef = useRef<string>("");

  // Debounced search whenever value changes.
  useEffect(() => {
    const q = value.trim();
    if (q.length < 2) {
      setSuggestions([]);
      return;
    }
    if (q === lastPickedRef.current) {
      // User just clicked a suggestion — don't immediately re-query for the same text.
      return;
    }
    lastQueryRef.current = q;
    const ctrl = new AbortController();
    const handle = setTimeout(async () => {
      try {
        const res = await api.get<PlaceSuggestion[]>(
          `/places/autocomplete?q=${encodeURIComponent(q)}`,
        );
        if (lastQueryRef.current === q) {
          setSuggestions(res);
          setHighlight(0);
          if (res.length > 0) setOpen(true);
        }
      } catch {
        // Silent — autocomplete failures aren't user-facing.
      }
    }, 220);
    return () => {
      clearTimeout(handle);
      ctrl.abort();
    };
  }, [value]);

  // Close on outside click.
  useEffect(() => {
    if (!open) return;
    function onDown(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  function pick(s: PlaceSuggestion) {
    lastPickedRef.current = s.label;
    onChange(s.label);
    setOpen(false);
    setSuggestions([]);
  }

  function onKey(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open || suggestions.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      pick(suggestions[highlight]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div ref={wrapRef} className="relative">
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={onKey}
        onFocus={() => suggestions.length > 0 && setOpen(true)}
        placeholder={placeholder}
        required={required}
        autoComplete="off"
        spellCheck={false}
        role="combobox"
        aria-autocomplete="list"
        aria-expanded={open}
        aria-controls={listId}
        className="field"
      />
      {open && suggestions.length > 0 && (
        <ul
          id={listId}
          role="listbox"
          className="absolute z-30 mt-1 max-h-72 w-full overflow-auto rounded-md border border-ink/15 bg-white shadow-lg"
        >
          {suggestions.map((s, i) => (
            <li
              key={s.place_id}
              role="option"
              aria-selected={i === highlight}
              onMouseDown={(e) => {
                e.preventDefault();
                pick(s);
              }}
              onMouseEnter={() => setHighlight(i)}
              className={`cursor-pointer px-3 py-2 text-sm ${
                i === highlight ? "bg-accent/10 text-ink" : "text-ink"
              }`}
            >
              <div className="font-medium">{s.primary}</div>
              {s.label !== s.primary && (
                <div className="text-xs text-ink/55">
                  {s.label.slice(s.primary.length + 2, -1)}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
