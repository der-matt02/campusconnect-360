"""API Gateway de CampusConnect 360.

Punto de entrada centralizado al ecosistema (patron API Gateway):
  - Autenticacion: emite y valida JWT.
  - Autorizacion: cada rol solo puede acceder a los servicios de su portal.
  - Enrutamiento: reenvia las peticiones a los microservicios.
  - Health agregado: estado de todos los servicios.
"""
import logging
import os

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .security import create_access_token, get_current_user
from .users import USERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gateway")

# Mapa de servicios: prefijo de ruta -> URL interna del microservicio.
SERVICES = {
    "academico": os.getenv("ACADEMICO_URL", "http://academico:8001"),
    "pagos": os.getenv("PAGOS_URL", "http://pagos:8002"),
    "notificaciones": os.getenv("NOTIFICACIONES_URL", "http://notificaciones:8003"),
    "asistencia": os.getenv("ASISTENCIA_URL", "http://asistencia:8004"),
    "analitica": os.getenv("ANALITICA_URL", "http://analitica:8005"),
}

# Autorizacion por rol: cada rol solo puede enrutar hacia los servicios de su portal.
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "academico": {"academico"},
    "pagos":     {"pagos"},
    "docente":   {"asistencia"},
    "director":  {"analitica", "notificaciones"},
}

app = FastAPI(
    title="CampusConnect 360 — API Gateway",
    description="Entrada centralizada con autenticacion JWT y enrutamiento a microservicios.",
    version="1.0.0",
)

# Permite que el frontend (React) consuma el Gateway.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/auth/login", tags=["auth"])
def login(req: LoginRequest):
    """Valida credenciales y emite un JWT."""
    user = USERS.get(req.username)
    if user is None or user["password"] != req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contrasena incorrectos",
        )
    token = create_access_token(req.username, user["role"], user["name"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "name": user["name"],
        "username": req.username,
    }


@app.get("/auth/me", tags=["auth"])
def me(current=Depends(get_current_user)):
    """Devuelve el usuario autenticado (valida el token)."""
    return current


@app.get("/health", tags=["infra"])
async def health():
    """Estado agregado del Gateway y de todos los microservicios (health checks)."""
    results = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in SERVICES.items():
            try:
                resp = await client.get(f"{url}/health")
                results[name] = "ok" if resp.status_code == 200 else "degraded"
            except httpx.HTTPError:
                results[name] = "down"
    overall = "ok" if all(v == "ok" for v in results.values()) else "degraded"
    return {"gateway": "ok", "services": results, "overall": overall}


@app.api_route(
    "/api/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    tags=["proxy"],
)
async def proxy(service: str, path: str, request: Request, current=Depends(get_current_user)):
    """Reenvia la peticion autenticada al microservicio correspondiente."""
    base_url = SERVICES.get(service)
    if base_url is None:
        raise HTTPException(404, f"Servicio '{service}' no existe")

    role = current.get("role", "")
    if service not in ROLE_PERMISSIONS.get(role, set()):
        logger.warning("Acceso denegado: rol '%s' -> servicio '%s'", role, service)
        raise HTTPException(403, f"El rol '{role}' no tiene acceso al servicio '{service}'")

    target = f"{base_url}/{path}"
    body = await request.body()
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length", "authorization")
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(
                method=request.method,
                url=target,
                params=request.query_params,
                content=body,
                headers=headers,
            )
    except httpx.HTTPError as exc:
        logger.error("Error al contactar %s: %s", target, exc)
        raise HTTPException(502, f"El servicio '{service}' no esta disponible")

    media_type = resp.headers.get("content-type", "application/json")
    return JSONResponse(
        status_code=resp.status_code,
        content=resp.json() if "application/json" in media_type else {"raw": resp.text},
    )
