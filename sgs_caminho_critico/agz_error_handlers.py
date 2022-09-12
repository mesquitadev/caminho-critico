import json
from json import JSONDecodeError
from typing import Union

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field

response_codes = {
            200: {"description": "success", "ssh_rc": 0},
            201: {"description": "success", "ssh_rc": 0},
            206: {"description": "partial", "ssh_rc": 206},
            401: {"description": "unauthorized", "ssh_rc": 161},
            403: {"description": "forbidden", "ssh_rc": 163},
            404: {"description": "not_found", "ssh_rc": 164},
            408: {"description": "timeout", "ssh_rc": 168},
            409: {"description": "business_exception", "ssh_rc": 169},
            417: {"description": "interrupted", "ssh_rc": 177},
            422: {"description": "format_error", "ssh_rc": 182},
            503: {"description": "third_party_error", "ssh_rc": 203},
            500: {"description": "failed", "ssh_rc": 1}
}


def select_response_codes(*codes):
    return {
        code: response_codes[code] for code in codes
    }


class AgilizaError(Exception):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return repr(self._value)


class AgilizaErrorsBaseModel(StarletteHTTPException):
    def __init__(self, info: str, status_code: int = None, error: str | dict | list = None):
        self.status_code = status_code
        self.status = response_codes[status_code]['description']
        self.error = self.set_detail(error)
        self.ssh_rc = response_codes[status_code]['ssh_rc']
        self.info = info
        super().__init__(status_code=self.status_code)

    @staticmethod
    def set_detail(error: str | dict | list):
        if type(error) != dict and type(error) != list:
            try:
                output = json.loads(error)
            except JSONDecodeError:
                output = {"error": error} if error is not None else None
            except TypeError:
                output = {"error": error} if error is not None else None
            return [output]
        elif type(error) == list:
            return error
        return [error]


class AgilizaPartialResponse(AgilizaErrorsBaseModel):
    def __init__(self, info: str):
        super().__init__(status_code=206, info=info)


class AgilizaUnauthorized(AgilizaErrorsBaseModel):
    def __init__(self, info: str, error: str | dict | list = None):
        super().__init__(status_code=401, info=info, error=error)


class AgilizaForbbiden(AgilizaErrorsBaseModel):
    def __init__(self, info: str, error: str | dict | list = None):
        super().__init__(status_code=403, info=info, error=error)


class AgilizaNotFound(AgilizaErrorsBaseModel):
    def __init__(self, info: str, error: str | dict | list = None):
        super().__init__(status_code=404, info=info, error=error)


class AgilizaTimeout(AgilizaErrorsBaseModel):
    def __init__(self, info: str, error: str | dict | list = None):
        super().__init__(status_code=408, info=info, error=error)


class AgilizaBusinessException(AgilizaErrorsBaseModel):
    def __init__(self, info: str, error: str | dict | list = None):
        super().__init__(status_code=409, info=info, error=error)


class AgilizaInterrupted(AgilizaErrorsBaseModel):
    def __init__(self, info: str, error: str | dict | list = None):
        super().__init__(status_code=417, info=info, error=error)


class AgilizaFormatError(AgilizaErrorsBaseModel):
    def __init__(self, info: str, error: str | dict | list = None):
        super().__init__(status_code=422, info=info, error=error)


class AgilizaThirdPartyError(AgilizaErrorsBaseModel):
    def __init__(self, info: str, error: str | dict | list = None):
        super().__init__(status_code=503, info=info, error=error)


class AgilizaException(AgilizaErrorsBaseModel):
    def __init__(self, status_code: int, info: str, error: str | dict | list = None):
        super().__init__(status_code=status_code, info=info, error=error)


async def agz_exception_handler(request: Request,
                                exc: Union[
                                    AgilizaPartialResponse,
                                    AgilizaUnauthorized,
                                    AgilizaForbbiden,
                                    AgilizaNotFound,
                                    AgilizaTimeout,
                                    AgilizaBusinessException,
                                    AgilizaFormatError,
                                    AgilizaThirdPartyError,
                                    AgilizaException
                                ]
                                ) -> JSONResponse:
    return JSONResponse(
        {"status": response_codes[exc.status_code]['description'],
         "info": exc.info,
         "detail": exc.error},
        status_code=exc.status_code)


class AgzBaseModelResponse(BaseModel):
    status: str
    result: dict


async def agz_response_handler(result: any, status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        {"status": "success", "status_code": status_code, "result": result},
        status_code=status_code)


class AgilizaErrorValidationResponse(BaseModel):
    status: str = Field(..., example="Status padrão agiliza")
    info: str = Field(..., example="Breve descrição do erro")
    detail: dict = Field(..., example=[
        {'loc': 'quantity',
         'msg': 'value is not a valid integer',
         'type': 'type_error.integer'}])
