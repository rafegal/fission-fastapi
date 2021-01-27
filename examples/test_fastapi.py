
# Required to decorate the function and the FastAPI to allow you to add on the internal route and can generate the documentation correctly.
from fastapi import APIRouter 


# Need to initialize to decorate the main function
router = APIRouter()

@router.get("/hello_fastapi")
async def main(request): # Mandatory use of "async
    return {"message": "Hello FastAPI"}
