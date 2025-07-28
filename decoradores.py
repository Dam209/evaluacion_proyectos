from functools import wraps
from flask import abort
from flask_login import current_user

def solo_rol(rol):
    def decorador(f):
        @wraps(f)
        def funcion(*args, **kwargs):
            if current_user.rol != rol:
                abort(403)
            return f(*args, **kwargs)
        return funcion
    return decorador