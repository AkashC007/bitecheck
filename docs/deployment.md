# Deployment

BiteCheck is prepared for public deployment but is not tied to a hosting
account. Deploy the backend first, then give its public URL to the frontend.
No API key or external data provider is required.

## 1. Deploy the FastAPI backend

Use the repository-root `Dockerfile` on any container host. It installs only
the API package and copies the committed configuration and synthetic analytics
artifacts.

The container:

- listens on `0.0.0.0:$PORT` (`8000` by default)
- exposes `GET /health` for health checks
- serves interactive documentation at `/docs`

If the host accepts a Docker build context, use the BiteCheck project root.
No backend environment variable is required for the committed dataset.

## 2. Deploy the Next.js frontend

Create a Node/Next.js service with `apps/web` as its root directory. Use:

```text
Build command: npm ci && npm run build
Start command: npm run start
```

Set this server-only environment variable in the frontend host:

```text
API_BASE_URL=https://your-public-api-host.example
```

Do not prefix it with `NEXT_PUBLIC_`; browsers do not need the backend address.
Redeploy the frontend after changing the value.

## 3. Public smoke check

After both services are live, verify:

1. `https://your-api-host/health` returns HTTP 200 and `status: ok`.
2. The frontend header reports that the search service is online.
3. **Build my recommendations** returns eight cards with the default filters.
4. **Only show walkable options** updates the result set.
5. Refreshing the public page produces no browser console errors.

## Security and operations notes

- `.env`, local virtual environments, build output, caches, and dependencies are
  excluded from Git and Docker build contexts.
- The app uses fictional committed data and requires no production secrets.
- GitHub Actions checks Python and TypeScript tests, linting, type safety, the
  production frontend build, and production npm dependencies.
- The JSON repository is intentionally appropriate for this small portfolio
  demo. A database, authentication, and real provider integrations are outside
  the showcase MVP.
