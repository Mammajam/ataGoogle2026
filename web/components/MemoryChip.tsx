"use client";

type Props = {
  visible: boolean;
  keys: string[];
};

export function MemoryChip({ visible, keys }: Props) {
  if (!visible) return null;
  return (
    <span className="sans inline-flex items-center gap-2 rounded-full bg-[#2f6f55] px-3 py-1 text-xs font-semibold text-white">
      Policy applied
      {keys.length > 0 ? <span className="font-normal opacity-80">{keys.join(", ")}</span> : null}
    </span>
  );
}
