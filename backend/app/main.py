from fastapi import FastAPI

app = FastAPI(
    title="Enterprise knowledge assistant",
    description="AI powered knowledge assistant for enterprise applications",
    version="0.1.0" 
)

@app.get("/")
def root():
    return {"message": "Welcome to Enterprise knowledge assistant"}

@app.get("/health")
def health():
    return {"status": "healthy"}    