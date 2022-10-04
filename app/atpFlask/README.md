# ATP Flask

## Obtener credenciales

1. Ir al backoffice de ATP https://intranet.despegar.com/atp-backoffice
2. _Manage Applications_
3. _Add Application_
4. Dejar _Method_ en _Create_, poner _Client ID_ que describa la aplicación (ej: risk-backoffice),
   _Contact Email_ que sea un mail del equipo que va a estar manteniendo la aplicación y
   _Description_ un resumen del proyecto. Submit.
5. Copiar _client secret_. _application key_ no lo necesité. _Continue_.
6. _Redirect urls_
7. _Add Url_
8. En _Url_ poner la URL de donde va a estar hosteado seguido de `/code`. Para correr localmente:
   `http://localhost:5000/code`. _Submit_.

## Dar acceso

1. Ir al backoffice de ATP https://intranet.despegar.com/atp-backoffice
2. _Manage Users_
3. Buscar usuario propio o al que se quiere dar acceso.
4. _Accesses_.
5. _Select Application_..
6. Seleccionar el _Client ID_ de la aplicación que se creo en el paso anterior.

## Configurar ambiente

1. Copiar `config.cfg.sample` a `config.cfg`.
2. En `ATP_CLIENT_ID` copiar lo que se puso en _Client ID_.
3. En `ATP_CLIENT_SECRET` lo que se obtuvo como _client secret_.
4. `ATP_ENVIRONMENT` se mantiene en `https://auth.despegar.com/` para usar el ambiente de
   producción.
5. La `SECRET_KEY` tiene que ser un string aleatorio. Se puede generar con el siguiente comando:
   `python -c 'import os; print(os.urandom(16))'`.

## Instalar el ambiente

### Proyecto propio

Para correr dentro de un proyecto propio, se puede instalar como dependencia:

`$ pipenv install 'git+ssh://git@github.com/despegar/atp-flask.git@master#egg=atp_flask'`

Hay que registrar un endpoint para tener como callback de ATP:

```py
from flask import Flask
import atp_flask

app = Flask(__name__)
app.config.from_envvar('MY_APP_SETTINGS')
atp_flask.register_code_url(app, '/code', '/')
```

Después se puede usar el decorador `@atp_flask.require_login(app)` para proteger las rutas que
necesitan un usuario con permisos.

```py
@app.route("/")
@require_login(app)
def index():
    # ...
```

Si se quiere obtener el email o cualquier otro dato provisto por ATP, se puede llamar a los métodos
`atp_flask.get_claims` o `atp_flask.get_email` pasando la aplicación como parámetro.

### Proyecto demo

Para correr el ejemplo demo incluido en este proyecto

`$ pipenv install`

## Correr el servidor

`$ ATP_SETTINGS=$(pwd)/config.cfg FLASK_DEBUG=1 FLASK_APP=index.py pipenv run flask run`

## Abrir con el browser

En el caso de un servidor local, ir a http://localhost:5000
