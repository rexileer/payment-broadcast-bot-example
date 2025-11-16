import os
import sys
import argparse
from pyrogram import Client
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')

# Типы сессий
SESSION_TYPES = {
    'bot': 'bot/s1_bot',       # для основного бота
    'checker': 'bot/s1_checker' # для сервиса проверки подписок
}

def create_session(session_type='bot'):
    """
    Создать файл сессии Pyrogram
    
    Args:
        session_type (str): Тип сессии (bot, checker)
    """
    if session_type not in SESSION_TYPES:
        print(f"Неизвестный тип сессии: {session_type}")
        print(f"Доступные типы: {', '.join(SESSION_TYPES.keys())}")
        return
        
    session_path = SESSION_TYPES[session_type]
    print(f"Создаем сессию типа: {session_type}")
    print(f"Путь к файлу сессии: {session_path}")
    
    # Создаем директорию, если не существует
    os.makedirs(os.path.dirname(session_path), exist_ok=True)
    
    app = Client(session_path, api_id=API_ID, api_hash=API_HASH)
    
    # Запускаем клиент для аутентификации
    print("Запуск клиента для аутентификации. Следуйте инструкциям...")
    app.run()
    print(f"✅ Сессия {session_type} успешно создана!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Создание сессии для Pyrogram')
    parser.add_argument('--type', dest='session_type', default='bot',
                        choices=SESSION_TYPES.keys(),
                        help=f'Тип сессии. Доступные: {", ".join(SESSION_TYPES.keys())}')
    
    args = parser.parse_args()
    create_session(args.session_type)
