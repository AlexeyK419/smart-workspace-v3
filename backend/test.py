"""
Диагностика авторизации GigaChat
Запуск: python debug_gigachat.py
"""
import base64
import httpx
import uuid
import warnings
from pathlib import Path

# Отключаем SSL предупреждения
warnings.filterwarnings("ignore")


def load_env_raw():
    """Читаем .env и показываем сырые значения"""
    env_path = Path(__file__).parent / ".env"
    
    if not env_path.exists():
        print(f"❌ Файл {env_path} не найден!")
        return {}
    
    clean_values = {}
    
    print("=" * 60)
    print("📄 СОДЕРЖИМОЕ .env ФАЙЛА (GIGACHAT_*):")
    print("=" * 60)
    
    with open(env_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if "GIGACHAT" in line and "=" in line and not line.strip().startswith("#"):
                key, _, value = line.partition("=")
                key = key.strip()
                raw_value = value.rstrip("\n\r")
                
                print(f"\n🔹 Строка {line_num}: {key}")
                print(f"   Сырое значение: [{raw_value[:60]}{'...' if len(raw_value) > 60 else ''}]")
                print(f"   Длина: {len(raw_value)} символов")
                
                # Очищаем
                clean = raw_value.strip().strip('"').strip("'").strip()
                print(f"   После очистки: [{clean[:60]}{'...' if len(clean) > 60 else ''}]")
                print(f"   Длина после очистки: {len(clean)} символов")
                
                # Проверяем на проблемы
                if raw_value != clean:
                    print(f"   ⚠️ Были лишние пробелы/кавычки!")
                else:
                    print(f"   ✅ Формат OK")
                
                clean_values[key] = clean
    
    return clean_values


def test_auth(auth_value, name):
    """Тестируем авторизацию"""
    AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    SCOPE = "GIGACHAT_API_PERS"
    
    print(f"\n{'─' * 50}")
    print(f"📤 Тест: {name}")
    print(f"   Header: Basic {auth_value[:25]}...{auth_value[-8:]}")
    
    try:
        rq_uid = str(uuid.uuid4())
        
        with httpx.Client(verify=False, timeout=30) as client:
            resp = client.post(
                AUTH_URL,
                headers={
                    "Authorization": f"Basic {auth_value}",
                    "RqUID": rq_uid,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                content=f"grant_type=client_credentials&scope={SCOPE}",
            )
        
        print(f"   Status: {resp.status_code}")
        
        if resp.is_success:
            data = resp.json()
            token = data.get("access_token", "")[:40]
            print(f"   ✅ УСПЕХ! Token: {token}...")
            return True
        else:
            try:
                error = resp.json()
                print(f"   ❌ Ошибка: {error.get('message', resp.text[:100])}")
            except:
                print(f"   ❌ Ошибка: {resp.text[:100]}")
            return False
                
    except Exception as e:
        print(f"   ❌ Исключение: {e}")
        return False


def main():
    print("\n" + "🔧 " * 15)
    print("   ДИАГНОСТИКА GIGACHAT")
    print("🔧 " * 15 + "\n")
    
    # 1. Читаем .env
    clean_values = load_env_raw()
    
    if not clean_values:
        print("\n❌ Не найдены GIGACHAT переменные в .env!")
        return
    
    client_id = clean_values.get("GIGACHAT_CLIENT_ID", "")
    client_secret = clean_values.get("GIGACHAT_CLIENT_SECRET", "")
    
    if not client_id:
        print("\n❌ GIGACHAT_CLIENT_ID пустой!")
        return
    
    # 2. Анализ типа данных
    print("\n" + "=" * 60)
    print("🔐 АНАЛИЗ:")
    print("=" * 60)
    
    is_uuid = len(client_id) == 36 and client_id.count("-") == 4
    is_long_key = len(client_id) > 50
    
    print(f"\nCLIENT_ID длина: {len(client_id)}")
    print(f"CLIENT_SECRET длина: {len(client_secret)}")
    
    if is_uuid:
        print("Тип ID: UUID (нужен SECRET)")
    elif is_long_key:
        print("Тип ID: Похож на готовый Authorization Key")
    
    # 3. Тестируем варианты
    print("\n" + "=" * 60)
    print("🧪 ТЕСТИРОВАНИЕ:")
    print("=" * 60)
    
    success = False
    
    # Вариант 1: Готовый ключ (если длинный)
    if is_long_key:
        success = test_auth(client_id, "CLIENT_ID как готовый ключ")
        if success:
            print("\n✅ Используйте CLIENT_ID напрямую (SECRET не нужен)")
            return
    
    # Вариант 2: client_id:secret → Base64 (стандартный)
    if client_secret:
        creds = f"{client_id}:{client_secret}"
        encoded = base64.b64encode(creds.encode()).decode()
        success = test_auth(encoded, "client_id:secret → Base64")
        if success:
            print("\n✅ Используйте пару CLIENT_ID + CLIENT_SECRET")
            return
    
    # Вариант 3: URL-safe Base64
    if client_secret:
        creds = f"{client_id}:{client_secret}"
        encoded = base64.urlsafe_b64encode(creds.encode()).decode()
        success = test_auth(encoded, "client_id:secret → Base64 URL-safe")
        if success:
            return
    
    # Ничего не сработало
    if not success:
        print("\n" + "=" * 60)
        print("❌ ВСЕ ВАРИАНТЫ НЕ РАБОТАЮТ")
        print("=" * 60)
        print("""
📋 ИНСТРУКЦИЯ:

1. Откройте https://developers.sber.ru/studio/
2. Войдите через Сбер ID
3. Выберите проект GigaChat (или создайте новый)
4. Раздел "Авторизационные данные"
5. Нажмите "Получить credentials"
6. Скопируйте Client ID и Client Secret

В файле backend/.env укажите БЕЗ КАВЫЧЕК:

GIGACHAT_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
GIGACHAT_CLIENT_SECRET=ваш_secret_здесь_без_кавычек

Сохраните и запустите этот скрипт снова.
""")


if __name__ == "__main__":
    main()