export const THEME_KEY = "greenchain.theme";

export type ThemePreference = "light" | "dark" | "system";

export const THEME_PREFERENCES: ThemePreference[] = ["light", "system", "dark"];

export const THEME_BOOTSTRAP = `(function(){
  try {
    var key = "${THEME_KEY}";
    var theme = localStorage.getItem(key) || "system";
    if (theme !== "light" && theme !== "dark") theme = "system";
    var dark = theme === "dark" || (theme !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches);
    var root = document.documentElement;
    root.classList.toggle("dark", dark);
    root.style.colorScheme = dark ? "dark" : "light";
    root.dataset.theme = theme;
  } catch (e) {}
})();`;

export function isThemePreference(value: string | null): value is ThemePreference {
  return value === "light" || value === "dark" || value === "system";
}

export function readThemePreference(): ThemePreference {
  try {
    const stored = localStorage.getItem(THEME_KEY);
    if (isThemePreference(stored)) return stored;
  } catch {
    /* private mode */
  }
  return "system";
}

export function prefersDark(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

export function resolveDark(preference: ThemePreference): boolean {
  return preference === "dark" || (preference === "system" && prefersDark());
}

export function applyTheme(preference: ThemePreference) {
  const dark = resolveDark(preference);
  const root = document.documentElement;
  root.classList.toggle("dark", dark);
  root.style.colorScheme = dark ? "dark" : "light";
  root.dataset.theme = preference;
  try {
    localStorage.setItem(THEME_KEY, preference);
  } catch {
    /* private mode */
  }
}
