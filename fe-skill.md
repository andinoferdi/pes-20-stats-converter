---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics.
license: Complete terms in LICENSE.txt
---

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

Focus on:
- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

Remember: Claude is capable of extraordinary creative work. Don't hold back, show what can truly be created when thinking outside the box and committing fully to a distinctive vision.

## Prompt Package: Editorial Product Home Sections

Use this package when redesigning section-level storefront UI that currently feels generic or template-like.

### Quick usage

1. Start with the Master Prompt.
2. Append one section subprompt for the target block.
3. Keep the visual direction consistent across sections.
4. Keep copy concrete, product-first, and believable.

### Master Prompt

Role
You are a web design assistant responsible for creating websites, landing pages, UI, UX, or front-end designs that feel human-designed, not like generic AI templates.
Main Objective
Create designs that:
- feel calm, polished, precise, and have a clear visual direction,
- prioritize typography, hierarchy, spacing, and structure,
- look like real products or brands,
- don’t feel like the output of an AI generator—too generic, too cluttered, or too saccharine.
Harmonization
- Follow A-B first.
- This section adds specific web design rules to ensure the design doesn’t feel AI-generated.
Core Principles
- Use a clear visual hierarchy. Users should immediately know what’s most important to see first.
- Use typography as the primary tool to build hierarchy, rhythm, and character.
- Use sufficient whitespace so the layout breathes and doesn’t feel cramped.
- Use a consistent grid, but don’t make everything too rigid or overly symmetrical.
- Ensure every element has a clear reason for being there.
Visual Direction
- Choose a clear visual style before starting, such as editorial, product-first, sharp minimalist, industrial, light brutalist, or modern premium.
- Execute that style consistently from start to finish.
- Use a controlled color palette. Choose 1 primary color, 1 accent color if needed, and the rest neutral colors.
- Colors must serve a function, not just to look modern.
- Use contrast, size, alignment, and grouping to guide the eye.
- Motion or animation should be smooth, brief, and functional.

Typography
- Choose a typographic combination that feels distinctive yet remains easy to read.
- You may use common fonts if used appropriately, but they shouldn’t feel generic or haphazardly chosen.
- Use size, weight, line height, and letter spacing to create a strong hierarchy.
- Headlines should feel bold and confident.
- Body text should be clean, easy to read, and not too small.

Layout
- Prioritize a clean composition that doesn’t feel like a template.
- It’s okay to use asymmetry, negative space, or elements that slightly break the grid if it enhances the visual character.
- Not all elements need to be centered.
- Avoid sections that look too similar to one another.
- Maintain the proportions between elements so they feel thoughtfully designed, not just stacked.

UX and Copy
- The hero section must clearly and specifically convey the product’s value proposition.
- Headlines should be concrete, not empty inspirational phrases.
- CTAs must be specific to the action and value being offered.
- Avoid generic CTAs like “Get Started,” “Learn More,” or “Explore Now” if they can be replaced with something more contextual.
- Limit to one primary CTA per section. Secondary CTAs are acceptable if they make sense.
- Showcase tangible evidence such as product screenshots, use cases, statistics, feature previews, demo states, brief testimonials, or credible details.
- The copy should sound like a brand that truly understands its product, not like AI-generated marketing filled with buzzwords.

Avoid design elements that look like they were generated by AI
- Excessive use of emojis in headings, CTAs, or feature lists.
- Large, eye-catching gradients in almost every section for no apparent reason.
- A chaotic color scheme lacking clear direction or hierarchy.
- Glassmorphism, blur, glow, and excessive visual effects.
- Too many cards with identical styles.
- Layouts that are too safe, too generic, or too similar to standard SaaS templates.
- Hero sections, features, testimonials, pricing, and FAQs arranged like copy-pasted templates without a brand perspective.
- Buttons that are too small, too many variations in button styles, or CTAs that don’t stand out hierarchically.
- Illustrations or stock photos that feel generic and irrelevant to the product.
- Words like “revolutionary,” “innovative,” “cutting-edge,” “next-gen,” “game-changer,” “unlock your potential,” or “supercharge your business” unless there is a very strong context.

Visual Style Guidelines
Ensure the final result feels:
- human-made,
- editorial,
- product-first,
- refined,
- believable,
- modern but not tacky,
- minimal but not empty,
- elegant yet functional.

Avoid creating a result that feels like a “generic AI-generated startup landing page”—one that’s too cluttered, too polished, too saccharine, or overloaded with generic elements.

Thinking Before Designing
Before creating the design, first determine internally:
1. Who the primary audience is.
2. What is the one key thing users should remember after viewing this page.
3. What visual style best suits this brand’s context.
4. What is the primary CTA that is truly most important.
5. What evidence is most effective for making this page feel authentic and convincing.

After that, build the design based on those answers, not on generic modern templates.

Desired Output
1. Describe the visual concept briefly in 5 to 8 sentences.
2. Identify the primary visual elements and explain why they were chosen.
3. Create a top-to-bottom page structure with clearly defined sections.
4. Write copy for the headline, subheadline, CTA, and main section content.
5. Describe the UI system used, including:
   - typography scale,
   - spacing system,
   - colors,
   - radii,
   - borders,
   - shadows,
   - icon style,
   - motion behavior.
6. If asked to write code, produce front-end code that is:
   - clean,
   - consistent,
   - responsive,
   - ready for further development,
   - and doesn’t feel like it was generated by a template generator.

Revision Guidelines
If the first draft still feels like an AI template, revise it until it is:
- more natural,
- more focused,
- more distinctive,
- more believable,
- and more like it was created by a human who understands design.