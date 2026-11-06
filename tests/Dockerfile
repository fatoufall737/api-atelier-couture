FROM python:3.11-slim

WORKDIR /code
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# L'API ne tourne pas en administrateur dans le conteneur
RUN useradd --create-home appuser && chown -R appuser /code
USER appuser

EXPOSE 8000

# 1) crée/met à jour le schéma  2) crée l'admin et le catalogue  3) lance l'API
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]