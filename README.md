# This project is still a work in progress

# Youtube-Shorts-Creator
Creates YouTube shorts.

This is the UI where users can input information about a reddit post:
<img width="1710" alt="Screenshot 2024-09-11 at 1 49 55 PM" src="https://github.com/user-attachments/assets/79b65c43-07e9-4813-8ccd-01e8c76a3e5b">

Once the information is inputed, a the request is sent to the backend, which creates the video. The backend creates the video and sends it back to the user to be displayed on screen.


https://github.com/user-attachments/assets/7a6e3186-0be9-435b-a855-894af0dffcd8


## Frontend (React + Vite)

A single-page app built with React Router, styled with Tailwind CSS v4 and managed with [Bun](https://bun.sh).

```bash
cd frontend
bun install
bun run dev      # http://localhost:3000
```

| Route | Page |
| --- | --- |
| `/` | Create a short from a Reddit post |
| `/history` | Search past requests and load one back into the editor |

The design tokens (colours, fonts, radii, type scale) live in `src/theme.css` as a Tailwind `@theme` block, so each one is available both as a utility (`bg-ink`, `rounded-card`, `text-display`) and as a CSS variable (`var(--color-ink)`). Shared class recipes for buttons, inputs and cards are in `src/components/ui.js`.

The app talks to `http://127.0.0.1:8000` by default. To change that, copy `frontend/.env.example` to `frontend/.env.local` and edit `VITE_API_URL`. Other scripts: `bun run build`, `bun run preview` and `bun run test` (Vitest + Testing Library).

## Backend (FastAPI)

Managed with [uv](https://docs.astral.sh/uv/); dependencies are in `pyproject.toml` and pinned in `uv.lock`.

Data is stored in PostgreSQL through SQLAlchemy, and the schema is managed with Alembic. A local Postgres 17 runs in Docker on port 5433, so it won't clash with other Postgres instances on 5432.

```bash
cd backend/api
cp .env.example .env              # optional, then edit
docker compose up -d              # start Postgres
uv sync
uv run alembic upgrade head       # create or upgrade the schema
uv run --env-file .env uvicorn app.main:app --reload --port 8000
```

After changing a model, generate a migration and review it before committing:

```bash
uv run alembic revision --autogenerate -m "describe the change"
```

Put the background clips (`SubwaySurfers.mov`, `MinecraftParkor.mov`, `MobileGamplay.mov`) in `backend/api/assets/backgrounds/`. Captions are rendered with ImageMagick, and `ffmpeg` must be installed.

| Endpoint | Description |
| --- | --- |
| `GET /shorts/` | Lists the available routes |
| `POST /shorts/create/` | Accepts a JSON or form body and returns the generated `short.mp4` |
| `GET /shorts/all/` | Lists every saved request |

Interactive docs are served at `/docs`.

Settings are read from environment variables (see `backend/api/.env.example`): `DATABASE_URL` (Postgres), `MEDIA_DIR`, `BACKGROUNDS_DIR`, `WHISPER_MODEL` (default `small`), `CAPTION_FONT` (an ImageMagick font name or a font file path, e.g. `/System/Library/Fonts/Supplemental/Futura.ttc`), `CORS_ORIGINS` (comma-separated).

### Tests

The tests run against a real Postgres. Each run creates its own temporary database (migrated with Alembic) and drops it at the end, so your dev data is never touched. Start Postgres first:

```bash
docker compose up -d
uv run pytest --cov=app
```

Set `TEST_DATABASE_URL` to use a different Postgres server.

The video pipeline tests stub out gTTS, ffmpeg, faster-whisper and moviepy, so they need neither network access nor the heavy dependencies.
