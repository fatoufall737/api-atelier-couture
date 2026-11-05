from fastapi import FastAPI

from app.routers import auth, utilisateurs

app = FastAPI(title="API Atelier de couture")

PREFIXE = "/api/v1"
ROUTEURS = (
    auth.router,
    utilisateurs.router,
)
for routeur in ROUTEURS:
    app.include_router(routeur, prefix=PREFIXE)


@app.get("/health")
def health():
    return {"status": "ok"}