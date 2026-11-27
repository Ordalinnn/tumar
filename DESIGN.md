# Тұмар — design system

One system for the site (`docs/`), the defense slides and the Streamlit demo (`app.py`).
The source of truth for values is `docs/style.css` section 1 (`:root`). If you change a token, change it there and here together.

## 1. Idea and principles

**Story.** One transfer is a dot and means nothing. Dots form a pattern. The pattern is the scheme. Every visual choice serves that sentence: things are drawn *from dots*, single dots stay quiet, and colour appears only where several dots add up to a signal.

**Scene.** A defense committee and bank anti-fraud staff looking at a projector or laptop in a dim room, plus Kazakh-speaking public on phones in the evening. That is why the ground is night, not paper.

1. **Dots, not lines.** Dividers, rails, borders of "special" objects and progress are rows of dots. Solid hairlines are for structure only (tables, the header seam).
2. **Silence by default, colour as a verdict.** Silver on night for everything. Carnelian means "alarm / main action", amber means "money at stake / final figure", mint means "safe / saved / consent given". Never use them as decoration.
3. **Explainable over impressive.** Numbers are shown in full (never truncated), with tabular figures, next to the words that explain them. Bad results are shown with the same weight as good ones.
4. **One authored motion moment per surface.** On the site: the amulet gathers from the stars and the warning card follows. Everything else is still and visible immediately.
5. **Two languages, one layout.** RU and KZ pages are structurally identical; Kazakh strings run ~10–20 % longer, so nothing has a fixed text width.

Mode: the site is a *Persuade/Read* surface (story first); the Streamlit demo is *Operate* (task first) — same tokens, quieter use of the motifs.

## 2. Colour

| Token | Hex | Use | Contrast on `--night-0` |
|---|---|---|---|
| `--night-0` | `#05070a` | page background | — |
| `--night-1` | `#0a0e11` | raised surface: panels, tables, terminal | — |
| `--night-2` | `#10171a` | inputs, table header if a fill is needed | — |
| `--night-3` | `#182226` | switch track, strong fill-border | — |
| `--silver` | `#ecf3ef` | body text, headings | 17.9 : 1 |
| `--silver-2` | `#aab6b1` | secondary text, descriptions | 9.6 : 1 |
| `--silver-3` | `#8b9792` | captions, footnotes, table headers (min. for text) | 6.7 : 1 |
| `--carn` | `#ff5a3c` | primary button, alarm, large numbers, h1 accent word | 6.5 : 1 |
| `--carn-hi` | `#ff8a70` | carnelian *small* text on night (signal labels, links in alarm context) | 8.8 : 1 |
| `--carn-deep` | `#b8301f` | bottom of the warning gradient | — |
| `--carn-ink` | `#1f0503` | text on carnelian | 6.3 : 1 on `--carn` |
| `--mint` | `#5ec8b4` | saved money, "ok", consent switch on | 10.0 : 1 |
| `--mint-hi` | `#7fe0cd` | the single biggest "saved" number | — |
| `--amber` | `#ffc45c` | money at stake, final figure, **focus ring** | 12.8 : 1 |
| `--dust` | `#9fb0c8` | star dust and horizon dots only (never text, never UI) | — |
| `--line` | `rgba(236,243,239,.16)` | default hairline / outline button border | — |
| `--line-soft` | `rgba(236,243,239,.09)` | panel border, table row rule | — |
| `--line-strong` | `rgba(236,243,239,.34)` | secondary button border, link underline | — |
| `--dot` / `--dot-faint` | `rgba(236,243,239,.5)` / `.24` | dotted dividers | — |

Warning surface: `linear-gradient(150deg, #c4361f, #b8301f)` with white text (5.4 : 1 at the lighter end). Selection: `rgba(255,90,60,.38)` with white text.

Rules: no gradient text; no glow halos on text (`text-shadow` is not used); glow is allowed only on the amulet canvas and the horizon embers. Lavender/violet was removed from the palette — `--dust` is a cool steel grey.

## 3. Typography

All three faces come from Google Fonts and were checked glyph-by-glyph (fontTools on the served woff2 files) for Cyrillic **and** Kazakh: ә ғ қ ң ө ұ ү һ і and capitals Ә Ғ Қ Ң Ө Ұ Ү Һ І — all present, all with `tnum`.

| Role | Family | Weights loaded | Fallback |
|---|---|---|---|
| Display (h1–h3, numbers, brand) | **Fira Sans Extra Condensed** | 700, 800 | `"Arial Narrow", system-ui, sans-serif` |
| Text (body, UI, buttons, tables) | **Golos Text** (variable) | 400–700 | `system-ui, "Segoe UI", Roboto, sans-serif` |
| Code (terminal only) | **Fira Code** | 400 | `ui-monospace, "Cascadia Mono", Consolas, monospace` |

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fira+Sans+Extra+Condensed:wght@700;800&family=Golos+Text:wght@400..700&family=Fira+Code:wght@400&display=swap">
```

Rejected after the glyph check (no Kazakh letters): Sofia Sans (all widths), Manrope, Unbounded, Jura, Wix Madefor, Alumni Sans, Yanone Kaffeesatz (partial), JetBrains Mono (partial). Bahnschrift is gone (Windows-only).

**Scale** (rem at 16 px root; fluid with `clamp`):

| Token | Size | Face / weight / line-height | Use |
|---|---|---|---|
| `--fs-hero` | 3.5 → 6 rem (56 → 96 px) | display 800 / .92 | h1 only |
| `--fs-statement` | 2.5 → 5 rem | display 800 / .94 | one centred verdict line, final heading |
| `--fs-h2` | 2.375 → 4.25 rem (38 → 68) | display 800 / .96 | section headings |
| `--fs-num` | 2.75 → 4.5 rem | display 800 / .9, tabular | ledger figures |
| `--fs-h3` | 1.375 → 1.625 rem | display 700 / 1.15 | step, signal, card titles |
| `--fs-title` | 1.25 rem | display 700 | panel titles |
| `--fs-lede` | 1.125 → 1.3125 rem | text 400 / 1.55 | lede, section sub, limits list |
| `--fs-body` | 1.0625 rem (17 px) | text 400 / 1.6 | body |
| `--fs-small` | .9375 rem (15 px) | text 400–500 / 1.55 | descriptions, captions |
| `--fs-micro` | .8125 rem (13 px) | text 500 | tags and chips inside the phone mock only |

Rules: sentence case everywhere, no letter-spaced uppercase labels, no eyebrow/kicker above headings (the heading speaks for itself), headings `text-wrap: balance`, paragraphs `pretty`, measure ≤ 62–74 ch. All numbers `font-variant-numeric: tabular-nums`. Typographic binding: `&nbsp;` before an em dash and inside numbers (`2&nbsp;154&nbsp;900&nbsp;₸`) so figures never break across lines.

## 4. Space, radius, depth

Spacing steps (4 px base): `--s-1` 4 · `--s-2` 8 · `--s-3` 12 · `--s-4` 16 · `--s-5` 24 · `--s-6` 32 · `--s-7` 48 · `--s-8` 64 · `--s-9` 96 · `--s-10` 128.
Section padding `--section-y` = clamp(80, 9vw, 136) px; heading-to-content gap `--head-gap` = clamp(40, 5vw, 64) px; page gutter `--gutter` = clamp(16, 4vw, 40) px; content width `--wrap` 1200 px. More space above a heading than below it.

Radii: `--r-xs` 6 · `--r-sm` 10 · `--r-md` 16 (images, inner boxes) · `--r-lg` 24 (panels) · `--r-xl` 32 (the rule simulator) · `--r-pill` 999 (buttons, chips, pills).

Depth (always offset downward, never a zero-offset coloured halo):
`--sh-1` `0 12px 28px -14px rgba(0,0,0,.85)` · `--sh-2` `0 40px 80px -40px rgba(0,0,0,.95)` · `--sh-carn` `0 14px 32px -16px rgba(255,90,60,.8)` (primary button only) · `--inset-top` `inset 0 1px 0 rgba(236,243,239,.06)` (top lip of panels).

## 5. Motion

| Token | Value | Use |
|---|---|---|
| `--ease-out` | `cubic-bezier(.23,1,.32,1)` | every enter, press, hover move |
| `--ease-in-out` | `cubic-bezier(.77,0,.175,1)` | on-screen morphs (rare) |
| `--t-press` | 140 ms | `:active` scale(.97) |
| `--t-fast` | 180 ms | colour / border changes |
| `--t-base` | 240 ms | small moves, switch knob, nav underline |
| `--t-enter` | 640 ms | hero entrance |
| `--t-moment` | 1400 ms | the one explanatory moment |

Choreography (site hero): h1 0 ms (lead, 16 px rise) → lede 90 → CTA row 160 → text link 200 → meta 240 (fade only) → the amulet gathers from stars on canvas (~1.7 s) → the warning card rises at 1100 ms (cause → effect). The canvas settles within 5 s. The radar sweeps once when first seen, then rests. The demo dot field lights once when seen (lost dots first, then a decelerating wave of saved dots).
Never: scroll-linked parallax, a fade-in on every section, tilt, infinite loops, count-up numbers. Hover motion only inside `@media (hover:hover) and (pointer:fine)`. `prefers-reduced-motion: reduce` → 200 ms opacity fades, no delays, canvases drawn in their final state.

## 6. Motifs and how to draw them

- **Dotted rule:** `background: radial-gradient(circle, rgba(236,243,239,.45) 1.2px, transparent 1.7px) 0 50% / 10px 8px repeat-x;` height 8 px. Vertical: same with `repeat-y` and `8px 10px`.
- **Dotted border:** `border: 2px dotted rgba(236,243,239,.2–.6)` (Chrome draws round dots at 2 px).
- **Amulet:** dotted silver triangle, carnelian inner triangle filled with dots, amber curls, five dotted pendants. Drawn procedurally in `docs/site.js` (`amulet()`, `tri()`, `line()`, `disc()`), each dot a radial sprite. Favicon/logo: dotted triangle + solid carnelian inner triangle (SVG in the page head).
- **Sky:** three sparse fixed dot layers (`body::before`), grain + vignette (`body::after`).
- **Horizon:** ember radial gradient at the bottom of hero/demo/final plus a dust-coloured dotted line 26–46 px above the section edge.
- **Growing markers:** timeline dots grow with the story (28 → 64 px); hot ones are carnelian dot-fills, the final one amber.
- **Dot field:** 1 dot = 10 000 ₸; 19 columns; carnelian = lost, mint = saved, dotted outline = scale key.

## 7. Components

**Buttons.** Primary: `--carn` fill, `--carn-ink` text, `--sh-carn`, pill, min-height 48 (44 small), 600 weight. Secondary: transparent, 1 px `--line-strong`, silver text. Hover (fine pointers): −1 px lift + lighter fill; press: `scale(.97)` 140 ms. External links carry a drawn arrow-up-right icon (1.75 stroke), never a Unicode glyph. Max two buttons per group; a third action becomes a text link.
**Text link.** Underline 1 px `--line-strong`, offset 5 px; hover → silver.
**Pill (static label).** 1 px `--line`, 14 px text, `--silver-2`. `hot` variant: carnelian 12 % fill, `#ffb7a6` text, leading carnelian dot.
**Chip / signal badge (toggle).** 2 px dotted border, leading 8 px ring; pressed = solid carnelian border, 16 % fill, ring filled. Min-height 44.
**Panel.** The only box: `--night-1`, 1 px `--line-soft`, `--r-lg`, `--sh-2` + `--inset-top`. Never put a panel inside a panel; inside, separate with spacing and dotted rules.
**Table.** Inside a panel with 8 × 16 px inset; header row 13 px `--silver-3` 600 with a dotted bottom rule; cells 14 × 12 px, `--line-soft` row rules, tabular figures; status colours: amber = bad, mint = ok, `--carn-hi` = partial. Wide tables scroll horizontally inside their panel (`tabindex=0`, labelled region) with a visible hint on small screens.
**Callout / footnote.** Small text in `--silver-3`, led by a 10 px dotted carnelian ring — never a coloured bar down one side.
**Warning card (the product's voice).** Carnelian gradient, radius 22/22/22/6 (speech bubble), display-700 title, white text, signal tags as dark translucent pills, followed by: silver solid "check licence", dust-outlined "second opinion", plain "continue".
**Switch.** 46 × 28 track `--night-3`; on = mint 24 % fill + mint knob.
**Focus.** 2 px solid amber outline, 3 px offset, everywhere.

## 8. Streamlit mapping (`.streamlit/config.toml`)

Streamlit 1.56 (installed) accepts `"<font name>:<css url>"` in `font`, `headingFont`, `codeFont`. Proposed theme:

```toml
[theme]
base = "dark"
primaryColor = "#ff5a3c"                 # --carn
backgroundColor = "#05070a"              # --night-0
secondaryBackgroundColor = "#0a0e11"     # --night-1 (sidebar, inputs, expanders)
textColor = "#ecf3ef"                    # --silver
linkColor = "#ff8a70"                    # --carn-hi
linkUnderline = true
codeTextColor = "#ecf3ef"
codeBackgroundColor = "#0a0e11"
font = "'Golos Text':https://fonts.googleapis.com/css2?family=Golos+Text:wght@400..700&display=swap"
headingFont = "'Fira Sans Extra Condensed':https://fonts.googleapis.com/css2?family=Fira+Sans+Extra+Condensed:wght@700;800&display=swap"
codeFont = "'Fira Code':https://fonts.googleapis.com/css2?family=Fira+Code:wght@400&display=swap"
baseFontSize = 16
headingFontWeights = [800, 800, 700, 700, 700, 700]
headingFontSizes = ["3.5rem", "2.5rem", "1.625rem", "1.25rem", "1.0625rem", "0.9375rem"]
metricValueFontSize = "2.75rem"          # pair with CSS to set the display face, see below
metricValueFontWeight = 800
baseRadius = "16px"                      # --r-md
buttonRadius = "999px"                   # --r-pill
borderColor = "#1c2427"                  # --line on night, flattened
dataframeBorderColor = "#141b1e"         # --line-soft flattened
dataframeHeaderBackgroundColor = "#10171a"  # --night-2
showWidgetBorder = true
redColor = "#ff5a3c"                     # alarm
orangeColor = "#ffc45c"                  # money at stake (amber)
yellowColor = "#ffc45c"
greenColor = "#5ec8b4"                   # saved / ok (mint)
blueColor = "#9fb0c8"                    # dust: neutral info
grayColor = "#8b9792"                    # --silver-3
chartCategoricalColors = ["#ff5a3c", "#5ec8b4", "#ffc45c", "#9fb0c8", "#ff8a70", "#aab6b1"]
chartSequentialColors = ["#1a0f0d", "#3b1610", "#5e1d13", "#842515", "#ab2f19", "#d23f2a", "#ff5a3c", "#ff7a5e", "#ff9d86", "#ffc2b4"]
```

Token → key map: `--carn`→`primaryColor`, `redColor`; `--night-0`→`backgroundColor`; `--night-1`→`secondaryBackgroundColor`, `codeBackgroundColor`; `--night-2`→`dataframeHeaderBackgroundColor`; `--silver`→`textColor`; `--silver-3`→`grayColor`; `--carn-hi`→`linkColor`; `--amber`→`orangeColor`/`yellowColor`; `--mint`→`greenColor`; `--dust`→`blueColor`; `--r-md`→`baseRadius`; `--r-pill`→`buttonRadius`; Golos Text→`font`; Fira Sans Extra Condensed→`headingFont`; Fira Code→`codeFont`.

Not expressible in config (needs a small `st.markdown("<style>…</style>", unsafe_allow_html=True)` block, using the CSS variables above): dotted dividers and dotted borders, the warning card gradient and speech-bubble radius, display face for `st.metric` values, tabular figures, amber focus ring, button press `scale(.97)` and hover gating, reduced-motion handling. Keep that CSS short and scoped to Streamlit's stable `data-testid` selectors; do not restyle Streamlit internals that change between versions.

Demo-specific guidance: the app is an Operate surface — use the dotted motifs for dividers and the timeline/test beads, keep panels flat (no panel inside an expander inside a container), keep colour for verdicts (warning = carnelian, saved = mint, at stake = amber), and keep the amulet to the header only.

## 9. Do / don't

| Do | Don't |
|---|---|
| Draw dividers and special borders with dots | Coloured bars down one side of a box |
| Let the heading speak; sentence case | Eyebrows/kickers, tracked uppercase labels, section numbers that carry no order |
| Show every number whole, tabular, bound with `&nbsp;` | Truncate amounts, animate counters |
| Colour = verdict (carnelian / amber / mint) | Lavender/violet, gradient text, text glow |
| One box level (panel); spacing and dotted rules inside | Cards inside cards (the phone mock in the hero is the only, deliberate exception) |
| Drawn SVG icons, 1.75 stroke, round caps | Unicode glyphs (☰ ↗ ↑ ×) as icons |
| 44 px minimum targets, hover only on fine pointers | Hover-only affordances, tilt, scroll parallax |
| Same structure in RU and KZ; test KZ at 320 px | Fixed-width labels sized to Russian strings |
