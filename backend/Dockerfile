FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV DATABASE_URL=postgresql://postgres:password123@postgres:5432/agripulse
ENV MQTT_HOST=mqtt-broker
ENV MQTT_PORT=1883

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
