# Free-tier deployment guide

The production image serves the React interface and FastAPI API from one Render web service. Neon provides PostgreSQL and pgvector. This keeps browser cookies same-origin and avoids a second paid service.

## 1. Create the Neon database

1. Sign in to Neon and create a free project in a nearby region.
2. Keep the default database and copy its connection string from **Connect**.
3. Treat the connection string as a secret. Do not commit it or paste it into screenshots.

The application accepts Neon's standard `postgresql://` connection string. It converts it to the async driver format and runs the database migrations during each deployment.

## 2. Create the Render service

1. Sign in to Render with GitHub.
2. Choose **New > Blueprint** and select `charan17kk/parcelpilot-ai-support-agent`.
3. Render reads `render.yaml` and proposes one free Docker web service.
4. Enter the two secret values requested by the Blueprint:
   - `DATABASE_URL`: the Neon connection string.
   - `OPENROUTER_API_KEY`: the existing OpenRouter key.
5. Apply the Blueprint and wait for the first deployment.

The expected URL is `https://parcelpilot-ai-support-agent.onrender.com`. If Render changes the service name or URL, update `FRONTEND_ORIGIN` to the exact public origin and redeploy.

## 3. Load the assessment data into Neon

The supplied PDFs and workbook are intentionally excluded from Git. Run the importer once from the project directory, using the private Neon URL locally:

```powershell
docker compose run --rm -e DATABASE_URL='<NEON_DATABASE_URL>' backend python -m scripts.ingest_data_pack --reset
```

Use single quotes around the URL in PowerShell because hosted database URLs contain `&` characters. This command reads the files already present in `data/raw/` and sends the parsed records and embeddings to Neon. It does not upload the raw files to GitHub or Render.

## 4. Verify the hosted application

1. Open `https://parcelpilot-ai-support-agent.onrender.com/api/v1/ready` and confirm every readiness value is `true`.
2. Open the main URL and sign in with one of the demo identities from the README.
3. Ask a deterministic order question and confirm citations appear.
4. Prepare an escalation, confirm it, and verify the completed action card.
5. Sign in as a different customer and verify account data remains isolated.

Render's free service can sleep after inactivity, so the first request after an idle period may take about a minute. Neon's free plan and OpenRouter's free-model limits are separate. The app reports a clear error if the AI provider quota is exhausted.

## Production limitations

- Demo authentication is intentionally mocked for the assessment; production should use ParcelPilot SSO.
- The free OpenRouter endpoint must not receive real confidential customer data.
- Render's free filesystem is ephemeral. Persistent business data is stored only in Neon.
- In-memory rate limits apply per running instance. A production rollout should use a shared limiter such as Redis.
