from fastapi import FastAPI
app = FastAPI()

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

@app.get("/mul10/{num}")
def mul_10(num: int):
    return {"result": num * 10}

@app.get("/getcode")
def get_code():
    return "Hello, CE"