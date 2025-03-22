from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from traceback import format_list, extract_tb


class UserError(Exception):
    status_code: int
    code: str

    def __init__(self, *args: object, status_code=400, code="bad_request") -> None:
        super().__init__(*args)
        self.code = code


class ServerError(Exception):
    pass


def _get_error_json(exception: Exception, debug: bool = False):
    error = {"name": getattr(exception, "code", "api_error"), "message": f"{exception}"}
    if debug:
        error["stack"] = format_list(extract_tb(exception.__traceback__))
    return error


def bind_exceptions(api: FastAPI, debug: bool = False):
    @api.exception_handler(UserError)
    async def user_error_handler(request: Request, exc: UserError):
        return JSONResponse(
            status_code=exc.status_code,
            content=_get_error_json(exc, debug=debug),
        )

    @api.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=_get_error_json(exc, debug=debug),
        )
