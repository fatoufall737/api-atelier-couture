from fastapi import FastAPI

app = FastAPI(title="API Atelier de couture")


@app.get("/health")
def health():
    return {"status": "ok"}