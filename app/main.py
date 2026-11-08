from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.deps import DbSession
from app.routers import auth, catalogue, clients, utilisateurs, mesures
from app.routers import commandes, commandes_edition, livraisons
from app.routers import statistiques

app = FastAPI(
    title="API Atelier de couture",
    description="Gestion des clients, mesures, commandes, paiements et livraisons.",
    version="1.0.0",
)


@app.exception_handler(RequestValidationError)
async def erreur_validation(request: Request, exc: RequestValidationError):
    """Les erreurs 422 ont la forme {"detail": "message"} (section 8 du sujet)."""
    messages = []
    for erreur in exc.errors():
        champ = ".".join(str(p) for p in erreur["loc"] if p != "body")
        message = erreur["msg"].removeprefix("Value error, ")
        messages.append(f"{champ} : {message}" if champ else message)
    return JSONResponse(status_code=422, content={"detail": " ; ".join(messages)})


PREFIXE = "/api/v1"

ROUTEURS = (
    auth.router,
    utilisateurs.router,
    clients.router,
    catalogue.router,
    mesures.router,
    commandes.router,
    commandes_edition.router,
    livraisons.router,
    statistiques.router,
)

for routeur in ROUTEURS:
    app.include_router(routeur, prefix=PREFIXE)


@app.get("/health", tags=["Santé"])
def health(db: DbSession):
    db.execute(text("SELECT 1"))  # le sujet demande de vérifier que la base répond
    return {"status": "ok"}