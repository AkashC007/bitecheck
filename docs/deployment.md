# Deployment

BiteCheck includes `render.yaml`, which creates the backend and frontend
together on Render. No API key or database is required. The public explorer
does require outbound HTTPS access to the City of Chicago open-data service;
the Analytics Lab uses committed artifacts.

## One-click Render deployment

Open the repository's **Deploy to Render** button, connect the public GitHub
repository, review the two free web services, and apply the Blueprint.

The Blueprint creates:

- `bitecheck-api`: the Dockerized FastAPI backend with `/health` monitoring
- `bitecheck-web`: the Next.js server connected to the API over Render's private
  network

Both services use the Ohio region and wait for GitHub CI checks before later
automatic deployments. Free web services sleep after inactivity, so the first
visit after a quiet period can take up to a minute; the frontend's production
health timeout allows that initial backend start to finish.

## Manual alternative: deploy the FastAPI backend

Use the repository-root `Dockerfile` on any container host. It installs only
the API package and copies the committed configuration and synthetic analytics
artifacts.

The container:

- listens on `0.0.0.0:$PORT` (`8000` by default)
- exposes `GET /health` for health checks
- serves interactive documentation at `/docs`

If the host accepts a Docker build context, use the BiteCheck project root.
No backend environment variable is required for the committed dataset.

## Then deploy the Next.js frontend

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

## Public smoke check

After both services are live, verify:

1. `https://your-api-host/health` returns HTTP 200 and `status: ok`.
2. The frontend header reports that the search service is online.
3. **Explore inspections** returns live official cards for Chicago Loop.
4. The **Fail** latest-result filter returns only failed latest inspections.
5. The **Synthetic analytics lab** tab retains the demo warning and existing
   recommendation behavior.
6. Refreshing the public page produces no browser console errors.

## Security and operations notes

- `.env`, local virtual environments, build output, caches, and dependencies are
  excluded from Git and Docker build contexts.
- The public explorer uses a live City open-data API without a production
  secret. The Analytics Lab uses a committed snapshot plus synthetic enrichment.
- GitHub Actions checks Python and TypeScript tests, linting, type safety, the
  production frontend build, and production npm dependencies.
- The JSON repository remains appropriate for the reproducible Analytics Lab.
  The live inspection provider is read-only; no user account or location is
  persisted.
