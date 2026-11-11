# Archivo: security.py
# Hash de contraseñas con sal (PBKDF2-HMAC-SHA256, solo biblioteca estándar).
# Cumple el RNF de seguridad: las contraseñas se guardan como hash, nunca en claro.
import hashlib
import hmac
import os

_ITERACIONES = 200_000


def hash_password(password: str) -> str:
    sal = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), sal, _ITERACIONES)
    return f"pbkdf2_sha256${_ITERACIONES}${sal.hex()}${dk.hex()}"


def verify_password(password: str, almacenado: str) -> bool:
    try:
        _alg, iteraciones, sal, esperado = almacenado.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                 bytes.fromhex(sal), int(iteraciones))
        return hmac.compare_digest(dk.hex(), esperado)
    except (ValueError, AttributeError):
        return False
