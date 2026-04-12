# Smart Student Workspace v3

Стек: Vue 3 + FastAPI + PostgreSQL + RouterAI (OpenAI-compatible API)

## Быстрый старт

```bash
# 1) Подготовить env
cp backend/.env.example backend/.env
#   -> заполнить DATABASE_URL и ROUTERAI_API_KEY

# 2) Создать БД в PostgreSQL
createdb workspace_db

# 3) Запустить проект
bash start.sh
```

Или вручную:

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (в другом терминале)
npm install && npm run dev
```

## Переменные окружения

```dotenv
DATABASE_URL=postgresql://postgres:password@localhost:5432/workspace_db
ROUTERAI_API_KEY=your_routerai_api_key
ROUTERAI_BASE_URL=https://routerai.ru/api/v1
ROUTERAI_MODEL=google/gemma-4-31b-it
ROUTERAI_TIMEOUT_SEC=60
```

Как сменить модель:
- поменяйте `ROUTERAI_MODEL` в `backend/.env`
- перезапустите backend

## AI Endpoints

- `POST /ai/chat`
- `POST /ai/courses/{id}/plan`
- `POST /ai/assignments/{id}/help`
- `GET /ai/models`

Полная документация API: `http://localhost:8000/docs`

## Backend AI Architecture

```text
backend/
├── config.py          # Settings (env)
├── llm_provider.py    # Универсальный LLM provider adapter (RouterAI)
├── routers/
│   └── ai.py          # AI endpoints, prompts, context assembly
└── test.py            # RouterAI smoke test
```

Примечание:
- Frontend API-контракты и backend endpoints сохранены.
- Миграция выполнена как замена provider layer без изменения пользовательского сценария.
