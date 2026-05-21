"use client";

/**
 * Four-point sparkle ("AI" glyph) with a rainbow-ish gradient fill.
 * Uses a stable random-ish gradient id so multiple instances on the same
 * page each have their own SVG definition.
 */
export function AISparkleIcon({
  className = "h-4 w-4",
}: {
  className?: string;
}) {
  const id = "ai-sparkle-grad";
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden>
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#f59e0b" />
          <stop offset="35%" stopColor="#ec4899" />
          <stop offset="70%" stopColor="#8b5cf6" />
          <stop offset="100%" stopColor="#3b82f6" />
        </linearGradient>
      </defs>
      <path
        fill={`url(#${id})`}
        d="M12 2.5c.5 0 .9.3 1.05.78l1.4 4.27 4.27 1.4c.48.15.78.55.78 1.05s-.3.9-.78 1.05l-4.27 1.4-1.4 4.27c-.15.48-.55.78-1.05.78s-.9-.3-1.05-.78l-1.4-4.27-4.27-1.4c-.48-.15-.78-.55-.78-1.05s.3-.9.78-1.05l4.27-1.4 1.4-4.27c.15-.48.55-.78 1.05-.78z"
      />
      <path
        fill={`url(#${id})`}
        d="M19 14.5c.3 0 .55.18.65.46l.65 1.95 1.95.65c.28.1.46.35.46.65s-.18.55-.46.65l-1.95.65-.65 1.95c-.1.28-.35.46-.65.46s-.55-.18-.65-.46l-.65-1.95-1.95-.65c-.28-.1-.46-.35-.46-.65s.18-.55.46-.65l1.95-.65.65-1.95c.1-.28.35-.46.65-.46z"
      />
    </svg>
  );
}
