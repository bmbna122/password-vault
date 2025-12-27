FROM python:3.12-slim

RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup
 
WORKDIR /app
COPY requirements.txt .
RUN  pip install --no-cache-dir -r requirements.txt

COPY app.py supabase_store.py ./
COPY templates ./templates
COPY static ./static

USER appuser

EXPOSE 8000

HEALTHCHECK CMD ["python","-c","import socket; s=socket.socket(); s.connect(('127.0.0.1',8000))"]

CMD ["python","-m","uvicorn","app:app","--host","0.0.0.0","--port","8000"]
