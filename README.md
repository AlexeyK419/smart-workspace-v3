# 🎓 Smart Student Workspace v3

**Стек:** Vue 3 + FastAPI + PostgreSQL + GigaChat (Sberbank LLM)

---

## Быстрый старт

```bash
# 1. Настроить окружение
cp backend/.env.example backend/.env
#    → Заполнить DATABASE_URL, GIGACHAT_CLIENT_ID, GIGACHAT_CLIENT_SECRET

# 2. Создать базу данных в PostgreSQL
createdb workspace_db

# 3. Запустить оба сервера
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

---

## Настройка .env

```dotenv
# PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/workspace_db

# GigaChat — получить на developers.sber.ru
GIGACHAT_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
GIGACHAT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GIGACHAT_SCOPE=GIGACHAT_API_PERS       # GIGACHAT_API_CORP для организаций
GIGACHAT_MODEL=GigaChat                # или GigaChat-Plus / GigaChat-Pro
```

---

## Как получить ключи GigaChat

1. Зарегистрируйтесь на **developers.sber.ru**
2. Перейдите в раздел **GigaChat API**
3. Создайте проект → получите `Client ID` и `Client Secret`
4. Вставьте в `backend/.env`

---

## API Endpoints

### AI (GigaChat)
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/ai/chat` | Чат с GigaChat (история сообщений) |
| POST | `/ai/courses/{id}/plan` | Генерация учебного плана курса |
| POST | `/ai/assignments/{id}/help` | Помощь с заданием |
| GET  | `/ai/models` | Список доступных моделей |

### Курсы, Материалы, Задания
| Метод | URL | Описание |
|-------|-----|----------|
| GET/POST | `/courses/` | Список / создание курсов |
| POST | `/courses/{id}/materials/` | Загрузка файла-материала |
| GET  | `/courses/{id}/materials/{mid}/download` | Скачать материал |
| POST | `/courses/{id}/assignments/` | Создание задания + файл |
| PATCH | `/courses/{id}/assignments/{aid}` | Обновить статус задания |
| GET  | `/courses/{id}/assignments/{aid}/download` | Скачать файл задания |

Полная документация: **http://localhost:8000/docs**

---

## Архитектура бэкенда

```
backend/
├── main.py          # FastAPI app, lifespan, seed данных
├── config.py        # Pydantic Settings — читает .env
├── database.py      # PostgreSQL через SQLAlchemy 2 + connection pool
├── models.py        # ORM: User, Course, Material, Assignment
├── schemas.py       # Pydantic запросы/ответы
├── gigachat.py      # GigaChat сервис:
│   ├── OAuth2 Client Credentials (кеш токена 30 мин)
│   ├── chat_complete(messages) → str
│   └── list_models() → list
└── routers/
    ├── ai.py          # /ai/chat, /ai/courses/{id}/plan, /ai/assignments/{id}/help
    ├── users.py
    ├── courses.py
    ├── materials.py   # multipart upload → диск
    └── assignments.py # Form Data + опциональный файл
```

## Поток аутентификации GigaChat

```
Приложение                      Sberbank IdP
    │                               │
    │── POST /oauth ──────────────►│
    │   Basic base64(id:secret)     │
    │   grant_type=client_creds     │
    │◄─ { access_token, expires_at }│
    │                               │
    │── POST /chat/completions ────►│  GigaChat API
    │   Bearer <token>              │
    │◄─ { choices[0].message } ────│
```
