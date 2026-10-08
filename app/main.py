from fastapi import FastAPI
from .database import Base, engine
from . import models  # noqa: F401  (registers tables)
from .routes import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bulk Certificate Generator")
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}