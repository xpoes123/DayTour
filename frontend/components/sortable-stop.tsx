"use client";

import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";

/**
 * Wraps a stop's row in a sortable container. The drag handle is the
 * `GripHandle` rendered inside `children` via the renderHandle prop;
 * pointer events anywhere else on the row stay unaffected so the X
 * button, notes textarea, carousel chevrons, etc. all keep working.
 */
export function SortableStop({
  id,
  children,
}: {
  id: string;
  children: (handleProps: {
    listeners: ReturnType<typeof useSortable>["listeners"];
    attributes: ReturnType<typeof useSortable>["attributes"];
    isDragging: boolean;
  }) => React.ReactNode;
}) {
  const { setNodeRef, transform, transition, listeners, attributes, isDragging } =
    useSortable({ id });
  const style: React.CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 10 : "auto",
  };
  return (
    <div ref={setNodeRef} style={style}>
      {children({ listeners, attributes, isDragging })}
    </div>
  );
}

export function GripHandle({
  listeners,
  attributes,
}: {
  listeners: ReturnType<typeof useSortable>["listeners"];
  attributes: ReturnType<typeof useSortable>["attributes"];
}) {
  return (
    <button
      type="button"
      aria-label="Reorder stop"
      title="Drag to reorder"
      className="absolute left-1.5 top-2 z-10 flex h-6 w-6 cursor-grab items-center justify-center rounded text-ink/40 transition hover:bg-ink/5 hover:text-ink active:cursor-grabbing"
      {...listeners}
      {...attributes}
    >
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor" aria-hidden>
        <circle cx="9" cy="6" r="1.5" />
        <circle cx="9" cy="12" r="1.5" />
        <circle cx="9" cy="18" r="1.5" />
        <circle cx="15" cy="6" r="1.5" />
        <circle cx="15" cy="12" r="1.5" />
        <circle cx="15" cy="18" r="1.5" />
      </svg>
    </button>
  );
}
