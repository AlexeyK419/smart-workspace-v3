# Smart Student Workspace v3

Frontend на Vue 3 + Vite, backend на FastAPI, PostgreSQL, RouterAI/OpenAI-compatible API.

## Локальная разработка

```bash
cp backend/.env.example backend/.env
npm install
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

В другом терминале:

```bash
npm run dev
```

## Продакшен

См. [DEPLOY.md](DEPLOY.md).
