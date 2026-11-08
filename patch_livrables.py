import os

dockerfile = """FROM python:3.13-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
"""

compose = """services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10

  api:
    build: .
    env_file: .env
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

volumes:
  pgdata:
"""

env_example = """DATABASE_URL=postgresql+psycopg://atelier:changez-moi@localhost:5432/atelier
SECRET_KEY=remplacez-par-une-cle-aleatoire-de-32-caracteres-minimum
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_EMAIL=admin@atelier.sn
ADMIN_PASSWORD=changez-moi
ADMIN_NOM_COMPLET=Mamadou (patron)

POSTGRES_USER=atelier
POSTGRES_PASSWORD=changez-moi
POSTGRES_DB=atelier
"""

open("Dockerfile", "w", encoding="utf-8").write(dockerfile)
if not os.path.exists("docker-compose.yml"):
    open("docker-compose.yml", "w", encoding="utf-8").write(compose)
open(".env.example", "w", encoding="utf-8").write(env_example)

g = open(".gitignore", encoding="utf-8").read() if os.path.exists(".gitignore") else ""
for ligne in (".env", "venv/", "__pycache__/", "*.pyc", "*.code-workspace", "test_unused.db"):
    if ligne not in g.splitlines():
        g += ("\n" if g and not g.endswith("\n") else "") + ligne + "\n"
open(".gitignore", "w", encoding="utf-8").write(g)
print("OK : Docker, .env.example et .gitignore prets")
