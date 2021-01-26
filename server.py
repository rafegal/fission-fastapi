"""
    This module is the main of the project. 
    It's responsible to run the application and render of requests.
"""
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.logger import logger
from pydantic import BaseModel
from fastapi.openapi.docs import get_swagger_ui_html
import importlib
import sys
import os
import logging
import uvicorn
import sentry_sdk

SENTRY_DSN = os.environ.get("SENTRY_DSN", None)
SENTRY_RELEASE = os.environ.get("SENTRY_RELEASE", None)

if SENTRY_DSN:
    params = {
        "dsn": SENTRY_DSN,
    }
    if SENTRY_RELEASE:
        params["release"] = SENTRY_RELEASE
    sentry_sdk.init(**params)


class Body(BaseModel):
    filepath: str
    functionName: Optional[str] = ""


def import_src(path):
    return importlib.machinery.SourceFileLoader("mod", path).load_module()


class FuncApp(FastAPI):
    def __init__(self, loglevel=logging.DEBUG):
        super(FuncApp, self).__init__()

        self.userfunc = None
        self.module = None
        self.root = logging.getLogger()
        self.ch = logging.StreamHandler(sys.stdout)

        self.root.setLevel(loglevel)
        self.ch.setLevel(loglevel)
        self.ch.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(self.ch)

        @self.post("/specialize", include_in_schema=False)
        def load(request: Request):
            logger.info("/specialize called")
            self.module = import_src("/userfunc/user")
            self.userfunc = self.module.main
            return ""

        @self.post("/v2/specialize", include_in_schema=False)
        def loadv2(body: Body):
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
                    self.module = importlib.import_module(moduleName, __package__)
                else:
                    self.module = importlib.import_module(moduleName)
            else:
                # load source from destination python file
                self.module = import_src(filepath)

            # load user function from module
            self.userfunc = getattr(self.module, funcName)
            logger.debug(self.userfunc)

            return ""

        @self.get("/healthz", include_in_schema=False)
        def healthz():
            return {}

        @self.api_route(
            "/",
            methods=["GET", "POST", "PUT", "HEAD", "OPTIONS", "DELETE"],
            include_in_schema=False,
        )
        async def f(
            request: Request,
            docs_func: Optional[str] = None,
            openapi_json: Optional[str] = None,
        ):
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

            # function added in the route to show in url docs if it does not exist yet.
            for route in self.routes:
                if self.module.__name__ in route.path:
                    break
            else:
                self.include_router(self.module.router)

            if openapi_json:
                return self.openapi()
            if docs_func:
                self.openapi_url = "?openapi_json=1"
                root_path = request.scope.get("root_path", "").rstrip("/")
                oauth2_redirect_url = self.swagger_ui_oauth2_redirect_url
                if oauth2_redirect_url:
                    oauth2_redirect_url = root_path + oauth2_redirect_url
                return get_swagger_ui_html(
                    openapi_url=self.openapi_url,
                    title="NOS Functions - Doc",
                    oauth2_redirect_url=oauth2_redirect_url,
                    init_oauth=self.swagger_ui_init_oauth,
                )

            return await self.userfunc(request)

        @self.middleware("http")
        async def sentry_exception(request: Request, call_next):
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                with sentry_sdk.push_scope() as scope:
                    scope.set_context("request", request)
                    user_id = "database_user_id"  # when available
                    scope.user = {"ip_address": request.client.host, "id": user_id}
                    sentry_sdk.capture_exception(e)
                raise e


app = FuncApp(logging.DEBUG)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
