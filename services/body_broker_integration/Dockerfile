FROM python:3.11-slim

WORKDIR /app

COPY requirements-complete.txt .
RUN pip install --no-cache-dir -r requirements-complete.txt

COPY services/ services/
COPY examples/ examples/
COPY training/data/ training/data/

CMD ["python", "-m", "services.body_broker_integration.server"]

