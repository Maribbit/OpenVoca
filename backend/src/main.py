from fastapi import FastAPI

app = FastAPI(title="OpenVoca API")


@app.get("/")
def read_root():
    return {"status": "ok", "message": "OpenVoca backend is running!"}
