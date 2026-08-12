---
name: GameHub
description: Free no-login casual games hub — dark navy stage, wooden boards, neon-red action, gold victories.
colors:
  night-deep: "#1a1a2e"
  night-surface: "#16213e"
  night-card: "#0f3460"
  hairline: "#2a2a4a"
  neon-red: "#e94560"
  neon-red-bright: "#ff6b6b"
  marquee-gold: "#ffd700"
  wood-light: "#f0d9b5"
  wood-dark: "#b58863"
  paper: "#fdfbf7"
  text-mist: "#eaeaea"
  text-dim: "#a0a0b0"
  leaf-green: "#4ade80"
  piece-black: "#1a1a1a"
typography:
  display:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "clamp(2.5rem, 6vw, 4rem)"
    fontWeight: 700
    lineHeight: 1.2
  headline:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.2
  title:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
    fontSize: "0.7rem"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "0.05em"
rounded:
  sm: "8px"
  md: "12px"
  pill: "999px"
spacing:
  xs: "8px"
  sm: "16px"
  md: "24px"
  lg: "32px"
components:
  button-primary:
    backgroundColor: "{colors.neon-red}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    padding: "16px 16px"
    typography: "{typography.title}"
  button-play:
    backgroundColor: "{colors.neon-red}"
    textColor: "#ffffff"
    rounded: "{rounded.sm}"
    typography: "{typography.title}"
  button-secondary:
    backgroundColor: "{colors.night-card}"
    textColor: "{colors.text-mist}"
    rounded: "{rounded.sm}"
    typography: "{typography.label}"
  category-chip:
    backgroundColor: "{colors.night-card}"
    textColor: "{colors.text-mist}"
    rounded: "{rounded.pill}"
    typography: "{typography.label}"
  category-chip-active:
    backgroundColor: "{colors.neon-red}"
    textColor: "#ffffff"
    rounded: "{rounded.pill}"
    typography: "{typography.label}"
  game-card:
    backgroundColor: "{colors.night-card}"
    textColor: "{colors.text-mist}"
    rounded: "{rounded.md}"
    padding: "24px 24px"
---

# Design System: GameHub

## Overview

**Creative North Star: "The Showcase Stage"**

The boards are the stars; the night around them stays quiet. GameHub is a dark theater where deep navy walls carry the page and the wood squares of each game board provide the warm, tactile surface under the light. Visitors browse a stage-lit arcade: cards float over a near-black navy, their 3px accent strip flicking on only when hovered, like a theater sign powering up.

The palette splits into two jobs. Navy layers (`night-deep`, `night-surface`, `night-card`) build a calm, low-chroma frame where nothing shouts. The neon red frames every moment of action — play buttons, active category tabs, selected moves, focus outlines — while marquee gold is reserved for victory and turn signals. Wood tones appear only where an actual game surface exists (checkers board, thumbnails), keeping the metaphor literal: wood is where the game happens, not decoration on glass.

Aesthetic character is quiet-night-with-glowing-stars: playful but unhurried. Density is generous and friendly — 8px radii on controls, 12px on cards, soft pills for filters, cloudy shadows that lift cards gently on hover. Text is near-white mist on dark navy, with dimmed secondary text for helpers. The interface is flat by default and lifts on state: shadow and translation are responses to interaction, never ambient decoration.

**Key Characteristics:**
- Dark navy theater frame with warm wood game surfaces
- Neon red as the sole "you can act here" signal
- Gold reserved for kings, turns, victories, and highlighting
- Flat by default; hover lifts cards and buttons with soft shadows
- Rounded and friendly: pills for filters, 8px buttons, 12px cards
- Boards and grids are the performers; UI recedes beside them

## Colors

A two-temperature night: cool navy stage, warm wood counter, one neon-red spotlight and one gold trophy light. Red is rare; its rarity is its power.

### Primary
- **Arcade Neon Red** (#e94560): The single "action" color of the system. Play buttons, active category tabs, selected word-search cells, active crossword letters, focus rings, hover borders, the card hover strip, and the destination of hover states everywhere. Always means "interact / go / now".
- **Neon Red Bright** (#ff6b6b): Hover step for red surfaces and red text accents. Same hue, lighter — the lamp turned up.

### Tertiary
- **Marquee Gold** (#ffd700): The reward color. Checkers kings and turn indicator, word-search star ratings, gold letters in hero gradients. Never used for navigation; always marks an earned or glowing state.

### Secondary (shared game surfaces)
- **Wood Light** (#f0d9b5) / **Wood Dark** (#b58863): The two checkerboard squares, board previews, and game thumbnails. Warm, earthy counter against cold navy.
- **Paper** (#fdfbf7): Crossword cell fill — the near-white "paper" where puzzle letters are written.
- **Leaf Green** (#4ade80): Confirmation green. Found word-search words, correct crossword letters, list `found` states. Crossed-out completion, not a brand color.

### Neutral
- **Night Deep** (#1a1a2e): App background. The dark theater floor.
- **Night Surface** (#16213e): Header, category nav bar, modal background, sidebar, panels. One step brighter than the floor.
- **Night Card** (#0f3460): Cards, buttons-secondary, thumbnails' chip background, list items, stat chips. The most common interactive surface.
- **Hairline** (#2a2a4a): Borders and dividers. Visible but never loud.
- **Text Mist** (#eaeaea): Primary text. Near-white on navy.
- **Text Dim** (#a0a0b0): Secondary text, captions, descriptions, helpers, panel headings.
- **Piece Black** (#1a1a1a): Checkers black pieces (vs. pure white pieces).

### Named Rules
**The One-Spotlight Rule.** Neon red appears on ≤10% of any given viewport as the single actionable accent. Rare enough that every red element reads as "press me now".
**The Gold-Access-Only Rule.** Gold is never a navigation color. It marks kings, earned stars, victory and glowing highlights — never a click target on its own.

## Typography

**Display Font:** System UI stack (`system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`)
**Label/Mono Font:** `"SF Mono", "Fira Code", monospace` — reserved for game data read-outs (timers, move history, word lists, captured counts).

The system pairs one generous system sans with a mono for readouts. No display font is loaded; hierarchy is carried by weight, size and a gradient. The hero title is the system's signature: the site name angled with a text gradient from mist to neon red and back, clipped to the glyphs.

### Hierarchy
- **Display** (700, `clamp(2.5rem, 6vw, 4rem)`, lh 1.2): The hero H1, "GameHub", drawn as a linear-gradient mist→red, background-clipped to text. Appears once per page and remains the only gradient text.
- **Headline** (700, 1.75rem, lh 1.2): Modal titles and panel-level identity.
- **Title** (600, 1.25rem, lh 1.4): Game card names.
- **Body** (400, 0.9rem, lh 1.5): Descriptions, rule text, helper copy. Dimmed as `text-dim` when secondary.
- **Label** (500, 0.7rem, ls 0.05em): Uppercased group headings (panel titles, badges) in `text-dim`.

### Named Rules
**The One-Gradient Rule.** Only the hero H1 may use a color gradient. Every other surface is flat; the gradient's singularity is its meaning.

## Layout

A single centered column capped at 1200px. The landing is one grid: `repeat(auto-fit, minmax(280px, 1fr))` game cards at 24px gaps, breathing from 32px page padding. A sticky category nav rides the top edge over the night surface.

Responsive behavior:
- ≤1024px: the game sidebar becomes a fixed off-canvas drawer sliding from the left; a round toggle button appears in the header.
- ≤768px: the category row collapses to a "Categorias" toggle opening a dropdown sheet; grids tighten to 16px gaps and 16px padding; the modal becomes single-column.
- ≤640px: crossword/word-search cells shrink to 26px; hero scales with the clamp.
- ≤480px: hero H1 at 2rem; the in-game menu hides entirely.

Boards stay centered in the free space beside the sidebar, up to 640×640 canvas scaled to fit; the word-search and crossword grids are tables capped to fit their container.

## Elevation & Depth

**Flat by default.** Depth exists only as a reaction to state. At rest, surfaces sit on the night floor separated by hairlines, not shadows. Hover, focus, modal layers, and current-turn states turn the lights on.

### Shadow Vocabulary
- **Ambient Lift** (`box-shadow: 0 4px 24px rgba(0,0,0,0.4)`): Game cards, board canvas. Appears on hover in combination with `translateY(-4px)` — the card lifts off the floor toward you.
- **Accent Glow** (`box-shadow: 0 8px 24px rgba(233,69,96,0.4)`): Primary button hover. Red light bleeding out onto the night.
- **Stage Curtain** (`background: rgba(0,0,0,0.7)`, + backdrop blur on hover overlays and `rgba(10,12,24,0.82)` on the play gate): Fullscreen modal and play-gate scrims that dim the board behind the current scene.

### Named Rules
**The Flat-By-Default Rule.** Surfaces are flat at rest. Shadows appear only as a response to hover, focus, or modal depth — shadow is the signal that something is now interactive, so it must be earned, not ambient.

## Shapes

Friendly, low aggression. The form language is a pill spectrum: fully rounded pills for filters and badges, `8px` for buttons and inputs, `12px` for cards and modals. Corners soften clickable targets; competition stays on the boards, not the chrome. Hover uses a 3px accent strip along the card's top edge (gradient red→gold) that fades in — a thin spotlight over the stage.

Borders are always the faint hairline (`#2a2a4a`); selected and active states trade the border color for red. No other recurring silhouettes: cutouts, notches and pleats are unused by design.

## Components

### Buttons
- **Shape:** Gently curved corners (8px); primary at full width of its container.
- **Primary (btn-primary):** Filled red gradient `linear-gradient(135deg, #e94560, #c0392b)`, white text, 16px padding, 1.1rem semibold. Hover: `translateY(-2px)` + the red ambient glow; active: back to flat.
- **Play (btn-play):** Flat red fill, white 600-weight text, 12px padding, full card width. Hover: brighter red + `scale(1.02)`; active `scale(0.98)`.
- **Secondary:** Night-card fill, hairline border, mist text, 8px radius. Hover darkens via hairline background.
- **Danger:** Red-tinted ghost — `rgba(233,69,96,0.15)` fill, red border, red text. Hover fills solid red with white text.
- **Focus:** 2px red outline offset 2px on every interactive element (`:focus-visible`).

### Chips & Tabs
- **Category chip:** Fully rounded pill, night-card fill, hairline border, mist text at 0.9rem. Hover: red border + brighter red text.
- **Active chip:** Solid red fill, white text — the one-spotlight moment of the nav.
- **Badge:** Tiny uppercase pill (0.7rem, 0.05em tracking), dim text, for metadata like player counts and durations.

### Cards / Containers
- **Corner Style:** Soft (12px).
- **Background:** Night card over the night-deep floor, 1px hairline border.
- **Shadow Strategy:** Ambient Lift only on hover, plus `translateY(-4px)`.
- **Hover Signal:** the 3px red→gold top strip fades in.
- **Internal Padding:** 24px scale (1.5rem).
- **Hover Overlay:** full-cover `rgba(0,0,0,0.75)` + backdrop blur revealing title, short description, rating/plays, and a Jogar button.

### Inputs / Fields
- **Style:** Night-card fill, hairline border, 8px radius, mist text, inherit font.
- **Focus:** 2px red outline offset 2px.
- **Checkbox/Radio:** red `accent-color` (`#e94560`).

### Navigation
- **Category bar:** sticky night-surface strip, hairline bottom border; pill tabs scrolling horizontally on desktop, dropdown sheet under a "Categorias" toggle ≤768px.
- **In-game header:** back circle button, centered status/timer, New Game + Resign actions; the sidebar drawer collapses ≤1024px.

### Signature Components
- **Board canvas (checkers):** 640×640 canvas with wood-light/wood-dark squares (CSS `#f0d9b5` / `#b58863`), radial-gradient white and black pieces, gold king highlight pulsing at `rgba(255,215,0,0.4→0.7)`, red legal-move highlights `rgba(233,69,96,0.3)`, soft drop shadow.
- **Word-search grid:** table of night-card cells, 40px (30px ≤480px), mono bold letters; red selection `rgba(233,69,96,0.5→0.2)`, green found `rgba(74,222,128,0.3)`.
- **Crossword grid:** paper-white cells (`#fdfbf7`) with 1.1rem bold ink and thin numbered corners; black blocks in night-card; red active outline, red-tinted highlight, green wrong-color corrections.
- **Category thumbnail:** gradient wood (dark→light) square with centered 4rem emoji icon floating on a 3s sine bounce for icon games; SVG mini-grids for checkers, word-search, and crossword.

## Do's and Don'ts

### Do:
- **Do** use night-deep/night-surface/night-card as the only three navy surfaces; stack them in that order for depth.
- **Do** reserve neon red for action moments, and gate it behind the one-spotlight rule (≤10% of any viewport).
- **Do** use gold only for earned states — kings, turns, stars, victory highlights — never navigation.
- **Do** keep cards flat at rest and lift on hover (`translateY(-4px)` + Ambient Lift shadow + the 3px red→gold top strip).
- **Do** use system sans everywhere and mono only for game read-outs (timer, move history, word lists, counts).
- **Do** put wood tones only where a real game surface or board is drawn.
- **Do** keep the hero H1 as the single gradient text on the page.

### Don't:
- **Don't** use shadows at rest; flat-by-default is the rule and shadow is earned by state.
- **Don't** introduce a second accent hue; red is the only action color and gold the only reward color.
- **Don't** load custom display fonts to "elevate" type; the system-sans weight-and-gradient hierarchy is the brand.
- **Don't** layer more than three navy stack levels on one surface.
- **Don't** put red or gold on decorative, non-interactive chrome.
- **Don't** let standalone game pages (snake, ant_defense, tower_defense) drift into their own palettes — they inherit this stage.