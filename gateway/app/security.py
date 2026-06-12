"""Seguridad del Gateway: emision y validacion de JWT."""
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from shared.config import SecurityConfig

bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(username: str, role: str, name: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=SecurityConfig.JWT_EXPIRE_MINUTES
    )
    payload = {"sub": username, "role": role, "name": name, "exp": expire}
    return jwt.encode(
        payload, SecurityConfig.JWT_SECRET, algorithm=SecurityConfig.JWT_ALGORITHM
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Valida el token JWT y devuelve el usuario. Protege las rutas del Gateway."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el token de autenticacion",
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            SecurityConfig.JWT_SECRET,
            algorithms=[SecurityConfig.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
        )
    return {
        "username": payload.get("sub"),
        "role": payload.get("role"),
        "name": payload.get("name"),
    }
