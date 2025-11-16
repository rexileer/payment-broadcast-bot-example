import os
import django
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

# Устанавливаем тип сервиса для правильного выбора сессии в config.py
os.environ["SERVICE_TYPE"] = "http"

# Добавляем путь к корню проекта в PYTHONPATH
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('http_server.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Импорты Django моделей после инициализации
from posting.models import PostingMessage
from bot.post_sender import send_posting

class PostingHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        logger.info(f"Получен POST запрос: {self.path}")
        
        if self.path.rstrip('/') == '/send_posting':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            try:
                logger.info(f"Запуск рассылки: {data}")
                send_posting(data)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode())
                logger.info("Рассылка запущена успешно")
            except Exception as e:
                logger.error(f"Ошибка при запуске рассылки: {e}", exc_info=True)
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            logger.warning(f"Неизвестный путь: {self.path}")
            self.send_response(404)
            self.end_headers()
            
    def log_message(self, format, *args):
        # Переопределяем стандартное логирование HTTPServer
        logger.info("%s - - [%s] %s" %
                     (self.address_string(),
                      self.log_date_time_string(),
                      format%args))

def run_server():
    port = int(os.getenv('BOT_HTTP_PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), PostingHandler)
    logger.info(f"🚀 Starting HTTP server on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("HTTP сервер остановлен")
    except Exception as e:
        logger.critical(f"Критическая ошибка в HTTP сервере: {e}", exc_info=True)
    finally:
        server.server_close()
        logger.info("HTTP сервер закрыт")

if __name__ == '__main__':
    run_server() 