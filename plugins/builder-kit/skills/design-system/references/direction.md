# Direction: choosing a visual world and committing to it

## 1. Surface mode decides ambition

| Mode | Job of the design | Good signals | Failure looks like |
|------|-------------------|--------------|--------------------|
| Tool | Help people finish tasks fast and without errors | Predictable layout, strong alignment, density control, keyboard shortcuts, calm neutrals + one accent, numbers in tabular figures | Marketing flourishes in a work tool: hero gradients, animated cards, low-contrast "aesthetic" text |
| Content | Make reading comfortable and findable | 60–75ch measure, generous line height, clear heading hierarchy, real typography, images with captions, TOC for long pages | Cards for everything, tiny gray text, centered long paragraphs |
| Persuade | Make one idea land and one action happen | A visual idea, a headline that says the value, proof (logos, numbers, testimonials), one primary CTA repeated, one authored motion moment | Template sections stacked (hero → 3 icon cards → logos → pricing → FAQ) with no idea |
| Experience | Create a memorable feeling | Expressive type, art direction, scroll-driven storytelling, sound/motion, surprise | Effects without meaning, slow pages, broken on mobile |

One product often has several modes: landing (Persuade), app (Tool), docs (Content). Each gets its own ambition level inside one shared token system.

## 2. Visual-world catalog

Each world is a coherent set of choices. Pick one per product, then adapt. `data/styles.csv` has the searchable version.

| World | Look | Best for | Avoid for |
|-------|------|----------|-----------|
| Quiet precision | Neutral grays, one saturated accent, 1px borders, small radii (4–8), tight spacing, mono for data | SaaS tools, dev tools, finance dashboards | Consumer lifestyle brands |
| Warm minimal | Off-white/cream backgrounds, warm grays, serif display + clean sans, soft radii | Wellness, coaching, boutique services, journaling | Dense data tools |
| Editorial | Big serif headlines, strong grid, rules and columns, image-led, restrained color | Media, blogs, portfolios, culture, premium brands | Forms-heavy tools |
| Swiss / International | Grid-driven, grotesk type, flush-left, strong scale contrast, primary colors or monochrome | Agencies, architecture, events, design-literate audiences | Playful kids' products |
| Soft product | Friendly rounded sans, large radii (12–20), pastel tints, soft shadows, illustrations | Consumer apps, education, family, onboarding-heavy apps | Enterprise security, legal |
| Bold color-block | Large flat color fields, oversized type, high contrast, few elements | Campaigns, launches, youth brands, events | Long-form reading |
| Dark technical | Near-black surfaces, luminous accent, fine borders, mono details, subtle glow only on focus | Developer tools, AI tools, security, crypto analytics | Health, kids, older audiences |
| Luxury restraint | Lots of space, thin weights, serif or high-contrast display, muted palette, slow motion | Fashion, hospitality, real estate, jewellery, perfume | Utility apps |
| Organic / natural | Earth tones, textured paper, hand-drawn accents, soft shapes | Food, sustainability, crafts, local businesses | Fintech |
| Neo-brutalist | Raw grids, thick borders, hard offset shadows, clashing color, system/grotesk type | Indie products, creative tools, portfolios that want attitude | Trust-critical products (banking, health) |
| Retro / nostalgic | Era-specific type and color (70s, 90s web, Y2K), grain, chunky UI | Music, games, culture, merch | Mainstream B2B |
| Glass / depth | Layered translucent panels with real backdrop blur over rich backgrounds, light borders | OS-like apps, media players, iOS-native feel | Low-end devices, text-heavy pages; never as decoration on flat backgrounds |
| Data-dense terminal | Monospace, grid tables, keyboard-first, minimal chrome | Trading, ops consoles, power-user tools | First-time consumers |
| Playful illustrative | Custom illustration system, bouncy motion, bright palette, characterful type | Kids, learning, games, community | Serious B2B |
| Arabic heritage modern | Arabic calligraphic or Kufi display, geometric patterns used sparingly, sand/ink/indigo palette, generous line height | Arabic-first brands, culture, hospitality, government services | Products with no Arabic audience (it becomes costume) |
| Gulf corporate clean | White space, deep green/navy/gold accents, IBM Plex Sans Arabic or Tajawal, bilingual layouts, formal tone | Banks, government, enterprise in the Gulf | Youth consumer apps |
| Monochrome ink | Black/white only, one weight contrast, photography carries color | Photographers, architects, fashion editorial | Data dashboards with states |
| Gradient mesh (earned) | Rich multi-stop mesh or grain gradient as a single brand moment, not on every element | Hero of AI/creative product launches | Repeated across cards, text and buttons |
| Material / native | Platform components, platform type and color roles | Android-first or iOS-first apps that should feel native | Brand-led marketing sites |
| Kinetic type | Type is the image: huge variable fonts, scroll-driven type motion | Agencies, events, launches | Reduced-motion-heavy audiences unless fallback is strong |

## 3. Proposing directions

Give 2–3 directions that differ on at least three axes (color temperature, type voice, shape, density, depth, motion, imagery). For each:

```
Direction A: "<name>"
Idea: <one sentence: what the user should feel and why it fits this product>
Color: <palette seed + where the accent appears>
Type: <display / body (Latin + Arabic)>
Shape & depth: <radii, borders vs shadows, elevation levels>
Density: <compact / comfortable / spacious>
Motion: <the one authored moment + micro-interaction tone>
Imagery: <photography / illustration / 3D / none, and its treatment>
Risk: <what could go wrong>
```

Pick the strongest for the brief when the user says "you decide", and say in one line why.

## 4. Turning the dial

**Bolder** (keep the world, raise commitment):
- Increase scale contrast: display 3–5× body size, tighter display tracking, heavier weight.
- Give the accent one big moment (a full-bleed section, a hero shape) instead of sprinkling it everywhere.
- Art-direct imagery: crop tight, consistent treatment (duotone, grain, angle).
- One authored motion moment (hero reveal, scroll-linked transition) instead of fades on everything.
- Break the grid once, on purpose.

**Quieter** (keep the world, lower noise):
- Neutralize: one accent, everything else from the neutral scale.
- Remove decorative shadows, gradients, borders. Use space to separate.
- Fewer type sizes and weights (≤ 2 weights per family).
- Unify radii to one or two values. Slow and shorten motion; remove looping animation.

## 5. `DESIGN.md` template

```markdown
# Design: <product>
Updated: <date> · Direction: <name> · Owner: <name>

## Brief
Product: <one line> · Users: <who> · Use scene: <where, device, light, attention>
Feel: <3 adjectives> · Never: <3 anti-adjectives>
Surface modes: landing = Persuade, app = Tool, docs = Content
Languages: ar (RTL, default) + en · Platforms: web, iOS, Android

## Direction
<the chosen direction block from §3, final>

## Tokens
Source of truth: `src/styles/tokens.css` (generated by palette.py + tokens.md scales)
- Color: brand <hex>, neutrals <tint>, semantic success/warning/danger/info, light + dark
- Type: Latin <display>/<body>, Arabic <display>/<body>; scale <ratio>, base <px>
- Space: 4px base, steps 0–16 · Radius: <values> · Elevation: <levels> · Motion: <durations/easings>

## Components
<list with variants and states; link to code>

## Rules
- One primary button per view.
- Icons: <library>, <stroke width>, <size steps>.
- Imagery: <treatment>.
- Copy voice: <tone, Arabic register (Modern Standard / Gulf colloquial for marketing?)>.

## Do / Don't
<project-specific examples>
```
