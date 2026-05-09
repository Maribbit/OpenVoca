# OpenVoca Frontend

This is the frontend component for OpenVoca, responsible for delivering the "Zen Mode" minimalist reading experience.

## Tech Stack
- **Framework**: [Vue 3](https://vuejs.org/) (Composition API)
- **Language**: TypeScript
- **Tooling**: [Vite](https://vitejs.dev/)
- **Routing**: Vue Router
- **Styling**: Tailwind CSS v4
- **Package Manager**: pnpm

## Development Setup

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build
```

## Testing & TDD

This project heavily enforces Test-Driven Development (TDD). 

- **Run Full Local Check**: `pnpm run check`
- **Run Unit Tests**: `pnpm test`
- **Run Tests with UI (UI Coverage)**: `pnpm vitest --ui` (if the UI package is installed)
- **Frameworks**: We use `vitest`, `jsdom`, and `@vue/test-utils` for rapid assertion and component-level testing.
Please write failing `.spec.ts` files inside the `/tests` folder *before* attempting complex logic implementation, and run `pnpm run check` before marking work as done.

## Architecture Guidelines
- **Single File Components**: Use `<script setup lang="ts">`.
- **UI/UX Aesthetics**: Zen Mode principles (paper-light background, ink text).
- **Styles**: Prefer Tailwind utility classes over custom CSS.

## Color System Guidelines

OpenVoca's theme colors are defined in `src/main.css` and exposed as Tailwind tokens. Use these tokens for neutral UI so light, dark, and palette variants stay consistent:

- `bg-paper` for page backgrounds and large quiet areas.
- `bg-surface` for panels, cards, modals, toasts, and tables.
- `text-ink` for primary text and active controls.
- `text-inkLight` for secondary text, hints, disabled states, and subtle icons.
- `bg-highlight` or `bg-selectionBg` only for intentional emphasis or selected text.

For subtle neutral borders, chips, and hover states, prefer token-based opacity classes such as `border-ink/8 dark:border-white/10`, `bg-ink/4 dark:bg-white/8`, and `hover:bg-black/4 dark:hover:bg-white/8`. Avoid using `gray-*` as a neutral panel or badge surface unless both light and dark behavior are explicitly handled.

Use Tailwind semantic colors only when the color carries meaning: `red-*` for destructive/error states, `emerald-*` or `green-*` for success, `blue-*` for informational/new states, and `rose-*` for negative vocabulary feedback. When semantic color appears on text or icons, pair it with a dark variant if contrast changes between themes, for example `text-blue-500 dark:text-blue-400`.
