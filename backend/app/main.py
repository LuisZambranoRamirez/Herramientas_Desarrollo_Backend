from fastapi import FastAPI

app = FastAPI(title="Soident API", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Soident API funcionando 🦷"}

@app.get("/health")
def health():
    return {"status": "OK", "service": "Soident Backend"}