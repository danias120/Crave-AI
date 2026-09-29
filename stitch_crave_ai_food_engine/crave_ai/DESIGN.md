---
name: Crave AI
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1b1b1b'
  surface-container: '#20201f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353535'
  on-surface: '#e5e2e1'
  on-surface-variant: '#e4bdbb'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#ab8886'
  outline-variant: '#5b403e'
  surface-tint: '#ffb3af'
  primary: '#ffb3af'
  on-primary: '#68000d'
  primary-container: '#cb202d'
  on-primary-container: '#ffe2e0'
  inverse-primary: '#bc1124'
  secondary: '#ffb59d'
  on-secondary: '#5d1900'
  secondary-container: '#b83900'
  on-secondary-container: '#ffddd2'
  tertiary: '#e9c400'
  on-tertiary: '#3a3000'
  tertiary-container: '#c9a900'
  on-tertiary-container: '#4c3e00'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad7'
  primary-fixed-dim: '#ffb3af'
  on-primary-fixed: '#410005'
  on-primary-fixed-variant: '#930017'
  secondary-fixed: '#ffdbd0'
  secondary-fixed-dim: '#ffb59d'
  on-secondary-fixed: '#390c00'
  on-secondary-fixed-variant: '#832600'
  tertiary-fixed: '#ffe16d'
  tertiary-fixed-dim: '#e9c400'
  on-tertiary-fixed: '#221b00'
  on-tertiary-fixed-variant: '#544600'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353535'
typography:
  headline-xl:
    fontFamily: Outfit
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Outfit
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-bold:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 40px
  container-max: 1280px
  gutter: 20px
---

## Brand & Style
The design system for this product centers on an **Energetic Modernism** aesthetic, tailored for a premium food discovery experience. It leverages a high-contrast dark mode to make food photography pop, creating an appetizing and immersive environment. The style blends **Sleek Dark Mode** principles with **Glassmorphism** highlights to denote AI-driven intelligence. The emotional response should be one of hunger, excitement, and effortless discovery. 

Key visual pillars include:
- **High-Impact Imagery:** UI elements act as a frame for vibrant, high-resolution food content.
- **Dynamic Glows:** Use of the brand gradient as a functional light source for AI-related interactions.
- **Precision Engineering:** Clean lines and purposeful spacing to signify the accuracy of the discovery engine.

## Colors
The palette is dominated by a deep, monochromatic dark base to ensure maximum contrast for food visuals. 

- **Primary Gradient:** The transition from Zomato Red to Orange is reserved for high-action items, AI search states, and primary call-to-actions.
- **Highlight Gold:** Specifically utilized for ratings, awards, and "premium" tier indicators.
- **Surface Strategy:** The background uses a solid `#1C1C1C`, while cards and elevated containers use `#2A2A2A`.
- **Accents:** Vibrant food-focused accents should be pulled dynamically from content where possible, otherwise defaulting to the secondary orange.

## Typography
The typographic hierarchy uses **Outfit** for all display and heading roles to inject personality and modern flair. Its geometric nature provides a "premium tech" feel. 

**Inter** is utilized for all functional text, including body copy, taglines, and ingredient lists, ensuring maximum legibility against dark backgrounds. 
- Use `headline-xl` for page titles and hero sections.
- Use `label-bold` for metadata like delivery times or price brackets.
- For AI-generated descriptions, use `body-md` with slightly increased line height (1.6) to improve scanability.

## Layout & Spacing
This design system utilizes a **12-column fluid grid** for desktop and a **4-column grid** for mobile. 

- **Grid Logic:** Use 24px margins for mobile and 40px+ for desktop to provide "breathing room" that mirrors a high-end editorial layout.
- **Rhythm:** All spacing must be a multiple of 4px. 
- **AI Search Context:** The primary search input should sit centered with significant vertical padding (`xl`) to act as the focal point of the home experience.
- **Card Layouts:** Use a masonry or tight-grid approach for restaurant discovery to emphasize variety.

## Elevation & Depth
Depth is conveyed through **Tonal Layering** and **Subtle Glows** rather than heavy traditional shadows.

- **Level 0 (Base):** `#1C1C1C` - The deep background.
- **Level 1 (Cards):** `#2A2A2A` - Used for restaurant cards and navigation bars. Feature a 1px border of `rgba(255, 255, 255, 0.05)` to define edges.
- **Level 2 (Modals/Popovers):** `#333333` - Used for detail views. These should include a subtle "Brand Glow" shadow: `0px 20px 40px rgba(0, 0, 0, 0.4)`.
- **AI Focus:** When the AI search is active, use a backdrop blur (12px) on the underlying content to pull the input into a distinct optical plane.

## Shapes
The shape language is consistently **Rounded**, reflecting a friendly and modern accessible brand.

- **Small Components:** Checkboxes and small tags use 4px (`rounded-sm`).
- **Standard UI:** Buttons, input fields, and standard list items use 12px (`rounded-md`).
- **Containers:** Large restaurant cards and the main AI search bar use 16px (`rounded-lg`).
- **Interactive Elements:** Category pills and rating badges use a full pill-shape (999px).

## Components
### AI Search Input
A prominent, oversized input field. Background should be `#2A2A2A` with a 2px gradient border on focus. Include a "Sparkle" icon to denote AI capabilities.

### Restaurant Cards
- **Image:** Top-weighted, 16:9 aspect ratio with 16px corner radius.
- **Content:** Title in `headline-lg`, subtitle in `body-sm` (muted color).
- **Badge:** The rating badge should be Gold (`#FFD700`) with black text, positioned in the top right of the image container.

### Buttons
- **Primary:** Gradient background (`primary_color_hex` to `secondary_color_hex`) with white text. Bold weight.
- **Secondary:** Ghost style with a 1px white or silver border.
- **Rating Chip:** Pill-shaped, semi-transparent background (`rgba(255, 215, 0, 0.1)`) with Gold text and icon.

### Navigation
A bottom-sticky navigation bar for mobile or a sleek top-blur bar for desktop. Use active-state indicators using the primary brand red.

### Selection Controls
Checkboxes and radios should use the primary orange for the "selected" state to ensure high visibility against the dark background.