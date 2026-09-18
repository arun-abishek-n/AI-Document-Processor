# AI Smart Document Processing — Frontend

React + TypeScript + Vite + Tailwind CSS + React Router UI: login/roles,
Document Types and Match Configurations management, and the batch
upload → confirm → match → results workflow. Talks to the FastAPI backend
(`../backend`) over REST — see the [root README](../README.md) for the full
project overview, architecture, and matching-engine explanation.

Routes: `/login`, `/dashboard`, `/document-types`, `/match-configs`,
`/users` (Admin only), `/process`, `/process/:id` — each protected by
`ProtectedRoute` (see `src/components/ProtectedRoute.tsx`), which redirects
unauthenticated visitors to `/login` and role-inappropriate ones to
`/dashboard`.

## Local development

```bash
cd frontend
npm install
cp .env.example .env   # point VITE_API_URL at your running backend
npm run dev
```

Opens at `http://localhost:5173`.

## Build

```bash
npm run build     # type-checks with tsc, then builds to dist/
npm run preview   # serve the production build locally
```

## Environment variables

See [.env.example](.env.example) — `VITE_API_URL` is the only one, and must
point at the deployed backend's base URL (no trailing slash, no hardcoded
`localhost` in production builds).
