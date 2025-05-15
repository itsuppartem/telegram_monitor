FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY admin_bot.py .
COPY .env .
COPY session.session .
CMD ["python", "admin_bot.py"] 