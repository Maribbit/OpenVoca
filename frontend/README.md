# OpenVoca Frontend

This is the frontend component for OpenVoca, responsible for delivering the "Zen Mode" minimalist reading experience.

## Tech Stack
- **Framework**: [Vue 3](https://vuejs.org/) (Composition API)
- **Language**: TypeScript
- **Tooling**: [Vite](https://vitejs.dev/)
- **Routing**: Vue Router
- **State Management**: Pinia
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

- **Run Unit Tests**: `pnpm test`
- **Run Tests with UI (UI Coverage)**: `pnpm vitest --ui` (if the UI package is installed)
- **Frameworks**: We use `vitest`, `jsdom`, and `@vue/test-utils` for rapid assertion and component-level testing.
Please write failing `.spec.ts` files inside the `/tests` folder *before* attempting complex logic implementation.

## Architecture Guidelines
- **Single File Components**: Use `<script setup lang="ts">`.
- **UI/UX Aesthetics**: Zen Mode principles (paper-light background, ink text).
- **Styles**: Prefer Tailwind utility classes over custom CSS.
