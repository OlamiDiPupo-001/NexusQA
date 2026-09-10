FROM python:3.14-slim

WORKDIR /app

COPY webhook_simulator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY webhook_simulator/ ./webhook_simulator/
COPY framework/ ./framework/

CMD ["python", "-m", "webhook_simulator.simulator"]