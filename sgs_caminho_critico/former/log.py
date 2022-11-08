import ipaddress
import json
from datetime import datetime
from typing import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute

import session as session
import former.persistence.log as persistence


class LogTransaction(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:

            try:
                ip = str(ipaddress.ip_address(request.client.host))
            except Exception:
                ip = None
            endpoint = request.url.path
            method = request.method
            begin_timestamp = datetime.now()

            try:
                arguments = await request.json()
            except Exception:
                arguments = None

            response: Response = await original_route_handler(request)

            end_timestamp = datetime.now()

            requester = session.get_var_value(var='requester')
            try:
                response_data = json.loads(response.body)
            except Exception:
                response_data = None

            # remocao da senha antes de gravar o log
            arguments_without_pass = arguments
            if "password" in arguments_without_pass:
                arguments_without_pass["password"] = "***"

            log = {
                "ip": ip,
                "requester": requester,
                "endpoint": endpoint,
                "method": method,
                "begin_timestamp": begin_timestamp,
                "arguments": arguments_without_pass,
                "return_code": response.status_code,
                "response_data": response_data,
                "end_timestamp": end_timestamp
            }

            await persistence.insert_log(log)

            return response

        return custom_route_handler
