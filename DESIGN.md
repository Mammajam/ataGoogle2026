# Design System Specification (DESIGN.md)

This document outlines the visual design language, token architecture, typography, color palette, component guidelines, and technical implementation for the application's design system.

---

## 1. Architectural Overview & Foundations

This design system is built on **Tailwind CSS v4** paired with a **shadcn/ui** structural paradigm. It utilizes modern Web platform features for dynamic, perceptually uniform theme resolution and component styling.

### Key Technical Pillars
* **Tailwind v4 First-Class Support**: Built using native CSS `@import 'tailwindcss';` and `@theme inline` declarations, eliminating legacy JavaScript config files (`tailwind.config.js`) in favor of direct CSS variable mapping.
* **OKLCH Color Space**: All palette primitives and semantic variables are expressed in the `oklch()` color model (Lightness, Chroma, Hue), ensuring predictable contrast calculation, smooth color transitions, and vibrant tones across light and dark modes.
* **Scoped Dark Mode**: Dark mode is controlled via custom CSS scoping using `@custom-variant dark (&:is(.dark *));`.
* **Micro-Interactions**: Integrated with `tailwindcss-animate` for fluid state transitions and dynamic loading fallbacks.

---

## 2. Color System & Semantic Tokens

The color palette is divided into two operational layers: **Core System Tokens** (semantic dynamic variables) and **Data Visualization Tokens** (chart series).

**Brand primary** is Spotify Green (`#1ED760` → `oklch(0.77 0.21 148.67)`). Labels on `--primary` fills use near-black (`--primary-foreground`), the pairing that green needs for contrast. Near-neutral ink (`--foreground`, `--border`) keeps a cool gray cast and is not retinted.

### 2.1 Base Palette & Semantic Mapping

| Token Name | Light Mode (OKLCH) | Dark Mode (OKLCH) | Purpose / Usage |
| :--- | :--- | :--- | :--- |
| `--background` | `oklch(1.00 0 0)` | `oklch(0 0 0)` | Canvas background |
| `--foreground` | `oklch(0.19 0.01 248.51)` | `oklch(0.93 0.00 228.79)` | Primary text and structural icon color |
| `--card` | `oklch(0.98 0.00 197.14)` | `oklch(0.21 0.01 274.53)` | Surfaces, cards, modal panels |
| `--card-foreground` | `oklch(0.19 0.01 248.51)` | `oklch(0.89 0 0)` | Text content on card surfaces |
| `--popover` | `oklch(1.00 0 0)` | `oklch(0 0 0)` | Floating menus, tooltips, dropdowns |
| `--popover-foreground` | `oklch(0.19 0.01 248.51)` | `oklch(0.93 0.00 228.79)` | Content inside popovers |
| `--primary` | `oklch(0.77 0.21 148.67)` | `oklch(0.77 0.21 148.67)` | Primary action buttons, active states |
| `--primary-foreground` | `oklch(0.15 0.00 0)` | `oklch(0.15 0.00 0)` | Text/icons rendered over `--primary` |
| `--secondary` | `oklch(0.19 0.01 248.51)` | `oklch(0.96 0.00 219.53)` | Secondary action controls, subtle badges |
| `--secondary-foreground` | `oklch(1.00 0 0)` | `oklch(0.19 0.01 248.51)` | Text/icons rendered over `--secondary` |
| `--muted` | `oklch(0.92 0.00 286.37)` | `oklch(0.21 0 0)` | Disabled backgrounds, table striping, faint fills |
| `--muted-foreground` | `oklch(0.19 0.01 248.51)` | `oklch(0.56 0.01 247.97)` | De-emphasized caption text, placeholders |
| `--accent` | `oklch(0.94 0.03 148.67)` | `oklch(0.19 0.04 148.67)` | Hover highlights, quiet selection states |
| `--accent-foreground` | `oklch(0.45 0.13 148.67)` | `oklch(0.77 0.21 148.67)` | Text/icons on accent elements |
| `--destructive` | `oklch(0.62 0.24 25.77)` | `oklch(0.62 0.24 25.77)` | Error states, dangerous actions, delete controls |
| `--destructive-foreground` | `oklch(1.00 0 0)` | `oklch(1.00 0 0)` | Text/icons on destructive buttons |
| `--border` | `oklch(0.93 0.01 231.66)` | `oklch(0.27 0.00 248.00)` | Divider lines, card outlines, input borders |
| `--input` | `oklch(0.98 0.00 228.78)` | `oklch(0.30 0.03 244.82)` | Form field element fill |
| `--ring` | `oklch(0.69 0.19 148.67)` | `oklch(0.69 0.19 148.67)` | Focus rings and outline indicators |

### 2.2 Sidebar Specific Palette

| Token Name | Light Mode (OKLCH) | Dark Mode (OKLCH) | Usage |
| :--- | :--- | :--- | :--- |
| `--sidebar` | `oklch(0.98 0.00 197.14)` | `oklch(0.21 0.01 274.53)` | Nav container background |
| `--sidebar-foreground` | `oklch(0.19 0.01 248.51)` | `oklch(0.89 0 0)` | Navigation text and icons |
| `--sidebar-primary` | `oklch(0.77 0.21 148.67)` | `oklch(0.77 0.21 148.67)` | Active navigation item indicator |
| `--sidebar-primary-foreground` | `oklch(0.15 0.00 0)` | `oklch(0.15 0.00 0)` | Text on active navigation item |
| `--sidebar-accent` | `oklch(0.94 0.03 148.67)` | `oklch(0.19 0.04 148.67)` | Hover state for nav items |
| `--sidebar-accent-foreground` | `oklch(0.45 0.13 148.67)` | `oklch(0.77 0.21 148.67)` | Text color on hovered nav items |
| `--sidebar-border` | `oklch(0.93 0.01 238.52)` | `oklch(0.38 0.02 240.59)` | Sidebar structural separator |
| `--sidebar-ring` | `oklch(0.69 0.19 148.67)` | `oklch(0.69 0.19 148.67)` | Sidebar interactive focus ring |

### 2.3 Data Visualization / Charting Palette

| Chart Token | OKLCH Value | Visual Color |
| :--- | :--- | :--- |
| `--chart-1` | `oklch(0.77 0.21 148.67)` | Spotify Green (Primary series) |
| `--chart-2` | `oklch(0.67 0.16 245.00)` | Electric Blue |
| `--chart-3` | `oklch(0.82 0.16 82.53)` | Warm Amber |
| `--chart-4` | `oklch(0.69 0.16 160.35)` | Vibrant Teal |
| `--chart-5` | `oklch(0.59 0.22 10.58)` | Deep Red / Coral |

---

## 3. Typography & Scale

The system relies on Google Fonts and clean web-safe stacks optimized for UI readability and computational layout display.

### 3.1 Font Families

* **Sans-Serif (`--font-sans`)**: `Open Sans, sans-serif` — Used for main body copy, UI components, headings, and navigation controls.
* **Monospace (`--font-mono`)**: `Menlo, monospace` — Used for code blocks, terminal elements, technical specs, and tabular data.
* **Serif (`--font-serif`)**: `Georgia, serif` — Reserved for long-form narrative content, editorial callouts, and block quotes.

### 3.2 Type Scale

| Token Name | CSS Value | Pixel Equivalent (16px base) |
| :--- | :--- | :--- |
| `--text-xs` | `0.75rem` | 12px |
| `--text-sm` | `0.875rem` | 14px |
| `--text-base` | `1rem` | 16px |
| `--text-lg` | `1.125rem` | 18px |
| `--text-xl` | `1.25rem` | 20px |
| `--text-2xl` | `1.5rem` | 24px |
| `--text-3xl` | `1.875rem` | 30px |
| `--text-4xl` | `2.25rem` | 36px |
| `--text-5xl` | `3rem` | 48px |

---

## 4. Elevation, Spacing & Geometry

### 4.1 Border Radius System
The UI relies on a highly rounded aesthetic (similar to contemporary mobile platforms).

* **Base Unit (`--radius`)**: `1.3rem` (~20.8px)
* **Small (`--radius-sm`)**: `0.875rem` (`calc(var(--radius) - 4px)` / override)
* **Medium (`--radius-md`)**: `1.3rem` (`calc(var(--radius) - 2px)`)
* **Large (`--radius-lg`)**: `1.625rem` (`var(--radius)`)
* **Extra Large (`--radius-xl`)**: `2rem` (`calc(var(--radius) + 4px)`)

### 4.2 Shadow Scale

* **`--shadow-sm`**: `0 1px 2px 0 rgb(0 0 0 / 0.05)`
* **`--shadow`**: `0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)`
* **`--shadow-md`**: `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)`
* **`--shadow-lg`**: `0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)`
* **`--shadow-xl`**: `0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)`
* **`--shadow-2xl`**: `0 25px 50px -12px rgb(0 0 0 / 0.25)`

---

## 5. Component Guidelines & Custom Utilities

### 5.1 Global Structural Rules
* High-level viewport reset ensures zero unwanted scrolling margins (`margin: 0; padding: 0; overscroll-behavior-x: none;`).
* All UI elements automatically adopt tokenized dynamic borders (`@apply border-border outline-ring/50;`).

### 5.2 Broken Image Fallbacks (`.broken-image-fallback`)
Provides graceful degradation for missing or failed images through smooth opacity fading (`fadeIn 0.3s ease-in-out`):
* **Light Mode**: `background: #f9fafb; border: 1px solid #e5e7eb;`
* **Dark Mode**: `background: #1f2937; border-color: #374151;`

---

## 6. Audit Findings & Refinement Opportunities

1. **Missing Typographic Variables**:
   * Section `@layer base` calls `var(--font-body)` and `var(--font-heading)`, but these are not defined in `:root` or `@theme`.
   * *Resolution*: Standardize `@layer base` to use `var(--font-sans)`.
2. **Low Light-Mode Contrast on Muted Text**:
   * `--muted-foreground` in `:root` shares the exact same OKLCH value as primary `--foreground` (`oklch(0.19 0.01 248.51)`), preventing visual de-emphasis.
   * *Resolution*: Adjust light mode `--muted-foreground` to a lighter contrast step like `oklch(0.50 0.01 248.51)`.

---

## 7. Visual Language (Reference Application)

The target UI is a **mobile-inspired, high-radius marketing/workspace shell**: clean white canvas, generous whitespace, Spotify-green primary actions, and pill-shaped controls. Use this section as the layout and component brief when implementing tokens from sections 2–5.

### 7.1 Page Canvas

* Full-bleed `--background` (white in light mode). No cream, paper, or editorial serif wash.
* Vertical scroll with a single column of stacked sections; inner content max-width is centered with large horizontal padding.
* Default type is `--font-sans` (Open Sans). Serif is reserved for quotes only.

### 7.2 Header

* Left: wordmark in `--foreground` sans, medium weight.
* Center: quiet text links (`--muted-foreground` after the section 6 contrast fix) for in-page anchors.
* Right: ghost text control + one pill primary CTA (`--primary` fill, `--primary-foreground` label, `--radius-xl` corners).
* Header sits on the same white canvas; no heavy bar, no colored brand strip.

### 7.3 Hero / Lead Block

* Two columns on desktop: copy left, media right; stacked on small viewports.
* Headline uses `--text-4xl` / `--text-5xl`, bold. Accent the second clause in `--primary` (example pattern: “Your Safety, **Our Priority.**”).
* Supporting paragraph is `--text-base` / `--text-lg` at `--muted-foreground`.
* Dual CTAs, both pills:
  * Primary: solid `--primary`, `--primary-foreground` (near-black) label, trailing arrow icon.
  * Secondary: `--accent` or light muted fill, `--accent-foreground` / `--foreground` label.
* Hero media uses `--radius-xl`, `--shadow-lg`, and may carry a small white overlay chip (`--radius-lg`, `--shadow-md`) on the lower-left of the image.

### 7.4 Feature / Capability Cards

* Three equal cards in a horizontal grid.
* Surface: `--card`, `--radius-xl`, `--shadow-md`, generous internal padding.
* Leading circular icon well (primary green, accent green, or warm `--chart-3` / `--chart-5` for variety).
* Bold card title + short `--muted-foreground` body.

### 7.5 Proof / Trust Block

* Left: section title, short body, then two rounded stat tiles. Stat figures use `--primary` at `--text-2xl`+; captions stay muted.
* Right: large testimonial / callout card — white, `--radius-xl`, `--shadow-md`, oversized decorative quotation mark in `--muted`, circular avatar, name + role.

### 7.6 Footer

* Minimal: wordmark + copyright left; small legal/support links right. No dense sitemap.

### 7.7 Mapping to GreenChain Surfaces

Apply the same geometry and tokens to the analyst workspace (not a marketing clone):

| GreenChain surface | Treatment |
| :--- | :--- |
| Workspace chrome | White canvas, sans wordmark, pill **Run audit** as the only primary CTA |
| Period pack dropzone | `--card` well, dashed `--border`, `--radius-xl`; demo-pack chip as a small white overlay |
| Inventory table | `--card` + `--shadow-md`; striped rows with `--muted`; numeric cells in `--font-mono` |
| Material / A2UI gate | Right-column card matching the testimonial treatment; confirm buttons use primary / secondary pills |
| Memory / policy chip | Small rounded badge on `--accent` with `--accent-foreground` |
| Destructive / failed run | `--destructive` text or button; never primary green |
| Scope / tCO₂e series | `--chart-1` … `--chart-5` if a breakdown chart is added |

### 7.8 Do Not Carry Forward

The previous `web/app/globals.css` cream/green/gold/Georgia tokens (`--cream`, `--green`, `--gold`, `--ink`) are superseded by this document. Brand green lives only on `--primary` / `--accent` / `--chart-1` (Spotify Green), never as a separate `--green` primitive. Do not mix those old primitives with the OKLCH semantic set.
