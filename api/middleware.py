import logging
import re

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


limiter = Limiter(key_func=get_remote_address)


class AuthorizationMaskFilter(logging.Filter):
    """
    Filtro de log que mascara o valor do header Authorization para evitar
    que tokens JWT apareçam em logs de acesso, erros ou debug.

    Substitui qualquer ocorrência de 'Bearer <token>' por 'Bearer [REDACTED]'.
    """
    _PATTERN = re.compile(r"(Bearer\s+)[A-Za-z0-9\-_\.]+", re.IGNORECASE)

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._PATTERN.sub(r"\1[REDACTED]", str(record.msg))
        if record.args:
            try:
                record.args = tuple(
                    self._PATTERN.sub(r"\1[REDACTED]", str(a)) if isinstance(a, str) else a
                    for a in (record.args if isinstance(record.args, tuple) else (record.args,))
                )
            except Exception:
                pass
        return True


def configurar_middleware(app: FastAPI):
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    _mask_filter = AuthorizationMaskFilter()
    for handler in logging.root.handlers:
        handler.addFilter(_mask_filter)
    logging.root.addFilter(_mask_filter)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        return response
