
from fastapi import FastAPI
from mangum import Mangum
from src.api_local.router import router
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os


load_dotenv()

env = os.getenv('ENVIRONMENT', None)


app = FastAPI(title='Test API',
              description='API ')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=f"/{env.lower() or 'v1'}")


@app.get("/")
def read_root():
    return {"Message": "Api deployed with aoricaan-src"}


# to make it work with Amazon Lambda, we create a handler object
handler = Mangum(app=app)
