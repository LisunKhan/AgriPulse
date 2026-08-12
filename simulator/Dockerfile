FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sensor.py .

ENV MQTT_HOST=mqtt-broker
ENV MQTT_PORT=1883
ENV PUBLISH_INTERVAL_SEC=5

CMD ["python", "-u", "sensor.py"]
