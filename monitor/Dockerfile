FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY telegram_monitor.py .
COPY .env .
COPY session.session .

CMD ["python", "telegram_monitor.py"] 