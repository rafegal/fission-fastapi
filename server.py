"""
    This module is the main of the project. 
    It's responsible to run the application and render of requests.
"""
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.logger import logger
from pydantic import BaseModel
import importlib
import sys
import os
import logging
import uvicorn

# app = FastAPI()


def import_src(path):
    return importlib.machinery.SourceFileLoader("mod", path).load_module()


class Body(BaseModel):
    filepath: str
    functionName: Optional[str] = ""


class FuncApp(FastAPI):
    def __init__(self, loglevel=logging.DEBUG):
        super(FuncApp, self).__init__()

        self.userfunc = None
        self.root = logging.getLogger()
        self.ch = logging.StreamHandler(sys.stdout)

        self.root.setLevel(loglevel)
        self.ch.setLevel(loglevel)
        self.ch.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(self.ch)

        @self.post("/specialize")
        def load(request: Request):
            logger.info("/specialize called")
            # load user function from codepath
            self.userfunc = import_src("/userfunc/user").main
            return ""

        @self.post("/v2/specialize")
        def loadv2(body: Body):
            # body = item.dict()
            logger.info(f"body: {body}")
            filepath = body.filepath
            handler = body.functionName
            logger.info(
                '/v2/specialize called with  filepath = "{}"   handler = "{}"'.format(
                    filepath, handler
                )
            )

            # handler looks like `path.to.module.function`
            parts = handler.rsplit(".", 1)
            if len(handler) == 0:
                # default to main.main if entrypoint wasn't provided
                moduleName = "main"
                funcName = "main"
            elif len(parts) == 1:
                moduleName = "main"
                funcName = parts[0]
            else:
                moduleName = parts[0]
                funcName = parts[1]
            logger.debug(
                'moduleName = "{}"    funcName = "{}"'.format(moduleName, funcName)
            )

            # check whether the destination is a directory or a file
            if os.path.isdir(filepath):
                # add package directory path into module search path
                sys.path.append(filepath)

                logger.debug('__package__ = "{}"'.format(__package__))
                if __package__:
                    mod = importlib.import_module(moduleName, __package__)
                else:
                    mod = importlib.import_module(moduleName)

            else:
                # load source from destination python file
                mod = import_src(filepath)

            # load user function from module
            self.userfunc = getattr(mod, funcName)
            logger.debug(self.userfunc)
            # return self.userfunc()

            return ""

        @self.get("/healthz")
        def healthz():
            return {}

        @self.api_route(
            "/", methods=["GET", "POST", "PUT", "HEAD", "OPTIONS", "DELETE"]
        )
        def f():
            if self.userfunc is None:
                print("Generic container: no requests supported")
                return HTTPException(status_code=500)
            #
            # Customizing the request context
            #
            # If you want to pass something to the function, you can
            # add it to 'g':
            #   g.myKey = myValue
            #
            # And the user func can then access that
            # (after doing a"from flask import g").

            return self.userfunc()


app = FuncApp(logging.DEBUG)


@app.get("/test")
def root_test():
    return {"content": "It's working!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
