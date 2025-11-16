FROM python:3.13

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем зависимости отдельно, чтобы использовать кэш
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код
COPY . .

# По умолчанию ничего не запускаем — будет переопределено в docker-compose
CMD ["python"]
