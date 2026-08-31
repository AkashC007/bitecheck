# BiteCheck web

Next.js frontend for the BiteCheck restaurant intelligence project.

## Run locally

Start FastAPI first, then run from this directory:

```bash
npm run dev
```

Open `http://localhost:3000`. Use `localhost` rather than `127.0.0.1` with the
development server so Next.js hot-reload resources use the same origin.

## Verify

```bash
npm test
npm run lint
npm run build
```

The test command compiles focused TypeScript contract tests into the ignored
`.test-dist` directory and runs them with Node.js's built-in test runner.

## Search request flow

The interactive form calls the same-origin
`GET /api/restaurants/search` Route Handler. Next.js forwards the query to
FastAPI using the server-only `API_BASE_URL` environment variable. This keeps
the backend address out of browser code and avoids requiring CORS locally.

The default backend URL is `http://127.0.0.1:8000`. Copy `.env.example` to an
ignored local environment file only when that URL needs to change. No API key
is required for the synthetic dataset.
