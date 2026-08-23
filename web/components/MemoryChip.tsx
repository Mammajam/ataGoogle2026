"use client";

type Props = {
  visible: boolean;
  keys: string[];
};

export function MemoryChip({ visible, keys }: Props) {
  if (!visible) return null;
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-accent px-3 py-1 text-xs font-semibold text-accent-foreground">
      Policy applied
      {keys.length > 0 ? <span className="font-normal opacity-80">{keys.join(", ")}</span> : null}
    </span>
  );
}
