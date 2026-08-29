"use client";

import { useEffect, useRef } from "react";

export function CursorGlow() {
  const glowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const glow = glowRef.current;
    if (!glow) return;

    const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const hover = window.matchMedia("(hover: hover) and (pointer: fine)");

    const syncVisibility = () => {
      const hide = motion.matches || !hover.matches;
      glow.hidden = hide;
      if (hide) glow.classList.remove("is-on");
    };

    syncVisibility();
    motion.addEventListener("change", syncVisibility);
    hover.addEventListener("change", syncVisibility);

    const onMove = (event: PointerEvent) => {
      if (glow.hidden) return;
      glow.style.transform = `translate3d(${event.clientX}px, ${event.clientY}px, 0)`;
      glow.classList.add("is-on");
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    return () => {
      motion.removeEventListener("change", syncVisibility);
      hover.removeEventListener("change", syncVisibility);
      window.removeEventListener("pointermove", onMove);
    };
  }, []);

  return <div ref={glowRef} className="cursor-glow" hidden aria-hidden />;
}
