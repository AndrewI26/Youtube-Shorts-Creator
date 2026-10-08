# This project is still a work in progress

# Youtube-Shorts-Creator
Creates YouTube shorts.

This is the UI where users can input information about a reddit post:
<img width="1710" alt="Screenshot 2024-09-11 at 1 49 55 PM" src="https://github.com/user-attachments/assets/79b65c43-07e9-4813-8ccd-01e8c76a3e5b">

Once the information is inputed, a the request is sent to the backend, which creates the video. The backend creates the video and sends it back to the user to be displayed on screen.


https://github.com/user-attachments/assets/7a6e3186-0be9-435b-a855-894af0dffcd8


## Backend (FastAPI)

```bash
cd backend/api
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Put the background clips (`SubwaySurfers.mov`, `MinecraftParkor.mov`, `MobileGamplay.mov`) in `backend/api/assets/backgrounds/`. Captions are rendered with ImageMagick, and `ffmpeg` must be installed.

| Endpoint | Description |
| --- | --- |
| `GET /shorts/` | Lists the available routes |
| `POST /shorts/create/` | Accepts a JSON or form body and returns the generated `short.mp4` |
| `GET /shorts/all/` | Lists every saved request |

Interactive docs are served at `/docs`.

Optional environment variables: `DATABASE_URL`, `MEDIA_DIR`, `BACKGROUNDS_DIR`, `WHISPER_MODEL` (default `small`), `CAPTION_FONT` (an ImageMagick font name or a font file path, e.g. `/System/Library/Fonts/Supplemental/Futura.ttc`), `CORS_ORIGINS` (comma-separated).

### Tests

```bash
pip install -r requirements-dev.txt
pytest --cov=app
```

The tests stub out gTTS, ffmpeg, faster-whisper and moviepy, so they run in under a second without network access or the heavy dependencies.
