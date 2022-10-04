import requests
from flask import Flask, redirect, request, url_for, session
import json
#from jose import jwt, exceptions
import base64
import python_jwt as jwt, jwcrypto.jwk as jwk, datetime
#from jose import exceptions
#import jwt

PREVIOUS_URL_NAME = "atp_flask_previous_url"


def redirect_uri():
    return '{scheme}://{host}{path}'.format(
        scheme=request.environ.get('HTTP_X_FORWARDED_PROTO', request.environ['wsgi.url_scheme']),
        host=request.environ.get('HTTP_X_FORWARDED_HOST', request.environ['HTTP_HOST']),
        path=url_for('code'),
    )


def read_id_token(app, id_token):
    key = select_proper_key(id_token, requests.get(app.config['ATP_ENVIRONMENT'] + 'keys').json()['keys'])
    try:
        jwkey = jwk.JWK.from_json(json.dumps(key))
        return jwt.verify_jwt(id_token, jwkey, ['RS256'], checks_optional=True)[1]
        #options = {'verify_signature': False}
        #return jwt.decode(id_token, key, audience=app.config['ATP_CLIENT_ID'], options=options)
        #return jwt.decode(id_token, key, audience=app.config['ATP_CLIENT_ID'])
    except Exception as e:
        return {}

def select_proper_key(token, atp_keys):
    try:
        header = json.loads(base64.b64decode(token.split('.')[0]+'===').decode("utf-8"))
        kid = header['kid']
        key = list(filter(lambda elem: elem['kid'] == kid, atp_keys))
    except Exception as e:
        return {}
    return key[0]

def get_claims(app):
    if 'id_token' in session:
        return read_id_token(app, session['id_token'])
    return {}


def get_email(app):
    return get_claims(app).get('email', None)


def login_url(app):
    return app.config['ATP_ENVIRONMENT'] + 'authorization?response_type=code&client_id={client_id}&scope=openid%20{client_id}%20u:email&redirect_uri={redirect_uri}'.format(
        client_id=app.config['ATP_CLIENT_ID'],
        redirect_uri=redirect_uri(),
    )


def require_login(app):
    def fun(f):
        def func(*args, **kwargs):
            if get_email(app) is not None:
                return f(*args, **kwargs)
            response = redirect(login_url(app))
            url = request.url
            https_url = url.replace("http", "https", 1)
            response.set_cookie(PREVIOUS_URL_NAME, https_url)
            return response
        func.__name__ = f.__name__
        return func
    return fun

def require_auth(app):
    def fun(f):
        def func():
            if "HTTP_AUTHORIZATION" in request.headers.environ.keys():
                auth = request.headers.environ["HTTP_AUTHORIZATION"]
                if ("Bearer " in auth and read_id_token(app, auth.split(" ")[1])):
                    return f()
                else:
                    return "invalid token", 500
            else:
                return "invalid request", 400
        func.__name__ = f.__name__
        return func
    return fun

def register_code_url(app, route='/code', default_url='/'):
    def code():
        id_token = requests.post(app.config['ATP_ENVIRONMENT'] + 'token', data={
            'grant_type': 'authorization_code',
            'client_id': app.config['ATP_CLIENT_ID'],
            'client_secret': app.config['ATP_CLIENT_SECRET'],
            'redirect_uri': redirect_uri(),
            'code': request.args['code'],
        }).json().get('id_token', None)

        if not id_token:
            return 'invalid code', 400

        decoded = read_id_token(app, id_token)
        if 'email' not in decoded:
            return 'invalid token', 400

        session['id_token'] = id_token
        previous_url = request.cookies.get(PREVIOUS_URL_NAME, None)

        if previous_url is not None:
            resp = redirect(previous_url)
            resp.set_cookie(PREVIOUS_URL_NAME, '', expires=0)
            return resp
        return redirect(default_url)
    app.route(route)(code)
