from fastapi import FastAPI
from routes.pharmacy import router as pharmacy_router
from routes.labtest import router as lab_router

#Create app

app = FastAPI(title = "Medicine, Lab Test Matcher API")

app.include_router(pharmacy_router)
app.include_router(lab_router)

@app.get("/")
def health_check():
    return {"Ready for mapping"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0",port = 8000, reload=True)