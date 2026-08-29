"use client";

import { useEffect, useState, type ReactNode } from "react";
import {
  applyTheme,
  readThemePreference,
  THEME_PREFERENCES,
  type ThemePreference,
} from "@/lib/theme";

const LABELS: Record<ThemePreference, string> = {
  light: "Light",
  system: "System",
  dark: "Dark",
};

function SunIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
      <circle cx="12" cy="12" r="3.5" />
      <path strokeLinecap="round" d="M12 3v1.6M12 19.4V21M4.6 4.6l1.1 1.1M18.3 18.3l1.1 1.1M3 12h1.6M19.4 12H21M4.6 19.4l1.1-1.1M18.3 5.7l1.1-1.1" />
    </svg>
  );
}

function SystemIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
      <rect x="3.5" y="5" width="17" height="12" rx="2" />
      <path strokeLinecap="round" d="M8 19h8" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
      <path
        strokeLinejoin="round"
        d="M18.5 14.2A7.2 7.2 0 0 1 9.8 5.5 7.4 7.4 0 1 0 18.5 14.2Z"
      />
    </svg>
  );
}

const ICONS: Record<ThemePreference, () => ReactNode> = {
  light: SunIcon,
  system: SystemIcon,
  dark: MoonIcon,
};

export function ThemeToggle() {
  const [preference, setPreference] = useState<ThemePreference>("system");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const initial = readThemePreference();
    setPreference(initial);
    applyTheme(initial);
    setMounted(true);

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onSystemChange = () => {
      const current = readThemePreference();
      if (current === "system") applyTheme("system");
    };
    media.addEventListener("change", onSystemChange);
    return () => media.removeEventListener("change", onSystemChange);
  }, []);

  function onSelect(next: ThemePreference) {
    setPreference(next);
    applyTheme(next);
  }

  if (!mounted) {
    return <div className="h-9 w-[108px] rounded-full border border-border bg-card" aria-hidden />;
  }

  return (
    <div
      role="radiogroup"
      aria-label="Color theme"
      className="inline-flex rounded-full border border-border bg-card p-0.5 shadow-sm"
    >
      {THEME_PREFERENCES.map((mode) => {
        const Icon = ICONS[mode];
        const selected = preference === mode;
        return (
          <button
            key={mode}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={LABELS[mode]}
            title={LABELS[mode]}
            onClick={() => onSelect(mode)}
            className={`flex h-8 w-8 cursor-pointer items-center justify-center rounded-full transition ${
              selected
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Icon />
          </button>
        );
      })}
    </div>
  );
}
