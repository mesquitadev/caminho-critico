import contextvars

Session = None
request_global = contextvars.ContextVar("request_global",
                                        default=dict())


# This is the only public API
# def g():
#     return request_global.get()

def get_var_value(var: str):
    try:
        return request_global.get()[var]
    except Exception:
        return None


def set_var_value(var: str, value):
    request_global.get()[var] = value
