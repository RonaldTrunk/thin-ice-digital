FROM python:3.12-slim

WORKDIR /app

COPY glacifraga-trading/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY glacifraga-trading /app
COPY assets /app/web/assets
COPY fonts /app/web/fonts

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
