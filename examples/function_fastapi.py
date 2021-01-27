# Required for attribute declaration that is used by FastAPI to generate the documentation
from pydantic import BaseModel 

# Required to decorate the function and the FastAPI to allow you to add on the internal route and can generate the documentation correctly.
from fastapi import APIRouter 

# Required to inform which parameter is optional
from typing import Optional

# Required for exception handling
from fastapi import HTTPException

# Need to initialize to decorate the main function
router = APIRouter()

# Statement the input parameters that will be shown automatically in the FastAPI documentation
class Request(BaseModel):
    # Optional = The parameter will be shown as not required in the FastAPI Documentation.
    # "Test" = default value, it is not mandatory to use but if used it will be shown in the FastAPI documentation.
    name: Optional[str] = "Test" 
    echo: str # Without using Optional, the parameter will be show as required in the FastAPI Documentation.

# /hello_api - It is the name that will be shown in the documentation.
# It is work just for the documentation
@router.post("/hello_fastapi")
async def main(request: Request): # Mandatory use of "async
    json_request = await request.json()   # It will load the input parameters in "json" format. The use of "await" is mandatory.
    # body_request = await request.body() # Alternative if the input is not in json format. The use of "await" is mandatory.
    name = json_request.get("name", "Test") # Get the parameter "name" if it exists, if it does not exist so "Test" is used as default.
    try:
        echo = json_request["echo"] #  This get format causes an error if the "echo" parameter does not exist.
    except KeyError: # Exception type for invalid key (parameter not informed)
        # Returns an exception, where it is possible to inform the error code and the problem information message
        raise HTTPException(status_code=400, detail="Echo parameter not found") 
    
    # Return in json format the processing of the function.
    return {"name": name, "echo": echo}
