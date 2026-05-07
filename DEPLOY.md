# Деплой

## Локальная разработка

Frontend:

```bash
npm install
npm run dev
```

Для режима разработки Vite создайте `.env.development` с содержимым:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

Backend:

```bash
cp backend/.env.example backend/.env
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Продакшен на одном VPS

```bash
cp .env.production.example .env.production
nano .env.production
docker compose --env-file .env.production up -d --build
```

Логи:

```bash
docker compose logs -f backend
docker compose logs -f web
docker compose logs -f db
```

Перезапуск:

```bash
docker compose --env-file .env.production up -d --build
```

Бэкап PostgreSQL:

```bash
docker compose exec db pg_dump -U workspace workspace_db > backup.sql
```

Восстановление бэкапа:

```bash
cat backup.sql | docker compose exec -T db psql -U workspace -d workspace_db
```

## Домен и HTTPS

Укажите домен на публичный IP VPS и обновите `CORS_ORIGINS` в `.env.production`.

Для HTTPS позже можно добавить TLS-слой перед стеком, например Caddy или Nginx с Certbot.

## Проверки

```bash
npm run build
python -m compileall backend
docker compose config
docker compose --env-file .env.production up -d --build
```

Проверить:

- frontend открывается
- `/api/docs` или `/api/openapi.json` доступны
- регистрация и логин работают
- загрузка файлов работает
- WebSocket-чаты работают
- запросы RouterAI работают, если задан `ROUTERAI_API_KEY`
