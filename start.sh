#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  Smart Student Workspace v3 — запуск одной командой
#  Использование: bash start.sh
# ─────────────────────────────────────────────────────────────────
set -e
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT_DIR/backend"

# ── 1. Проверить .env ─────────────────────────────────────────
if [ ! -f "$BACKEND/.env" ]; then
  echo "⚠️  Файл backend/.env не найден."
  echo "   Копирование из .env.example..."
  cp "$BACKEND/.env.example" "$BACKEND/.env"
  echo ""
  echo "   Откройте backend/.env и заполните:"
  echo "     DATABASE_URL       — строка подключения к PostgreSQL"
  echo "     GIGACHAT_CLIENT_ID — ID из developers.sber.ru"
  echo "     GIGACHAT_CLIENT_SECRET"
  echo ""
  read -p "   Нажмите Enter, когда будете готовы..."
fi

# ── 2. Backend ────────────────────────────────────────────────
echo ""
echo "🐍 Запуск Python-бэкенда..."
cd "$BACKEND"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements.txt
echo "   Зависимости установлены."
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
echo "   Бэкенд запущен (PID $BACKEND_PID) → http://localhost:8000"

# ── 3. Frontend ───────────────────────────────────────────────
echo ""
echo "⚡ Запуск Vue-фронтенда..."
cd "$ROOT_DIR"
if [ ! -d "node_modules" ]; then
  npm install
fi
npm run dev &
FRONTEND_PID=$!
echo "   Фронтенд запущен (PID $FRONTEND_PID) → http://localhost:5173"

# ── 4. Open browser ───────────────────────────────────────────
sleep 3
command -v xdg-open &>/dev/null && xdg-open http://localhost:5173 || true
command -v open     &>/dev/null && open     http://localhost:5173 || true

echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✅ Фронтенд  →  http://localhost:5173"
echo "  ✅ API docs  →  http://localhost:8000/docs"
echo "  🤖 GigaChat и PostgreSQL настраиваются в backend/.env"
echo "  Ctrl+C — остановить оба сервера"
echo "═══════════════════════════════════════════════════"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Серверы остановлены.'" EXIT
wait
