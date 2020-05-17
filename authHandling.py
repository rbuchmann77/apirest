# -*- coding: utf-8 -*-
from apirest import app

from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from starlette.middleware.authentication import AuthenticationMiddleware

from starlette_auth_toolkit.backends import MultiAuth
from starlette_auth_toolkit.base.backends import BaseBasicAuth
from starlette.authentication import (
    AuthenticationBackend,
    AuthCredentials,
    requires,
    #BaseUser,
)

from repositories import Users, Tokens, Session
from sqlalchemy import exc
from datetime import datetime

from starlette_auth_toolkit.cryptography import (
    PBKDF2Hasher,
    #generate_random_string,
)

from starlette.responses import JSONResponse, PlainTextResponse

# Password hasher
hasher = PBKDF2Hasher()

@app.route("/users/register", methods=["POST"])
async def register_user(request):
    credentials=await request.json()
    user = Users(
        username=credentials["username"],
        username_canonical=credentials["username"].lower(),
        email=credentials["email"],
        email_canonical=credentials["email"].lower(),
        enabled=1,
        password=await hasher.make(credentials["password"]),
        last_login=datetime.now()
    )

    try:
        session = Session()
        session.add(user)
        session.commit()
    except exc.SQLAlchemyError:
        return JSONResponse({"message": "username or email already used", "code": "1"}, status_code=409)

    return JSONResponse({"username": user.username}, status_code=201)

@app.route("/users", methods=["DELETE"])
@requires("authenticated")
async def delete_user(request):
    try:
        session = Session()
        session.query(Users).filter_by(id=request.user.id).delete()
        session.commit()
    except exc.SQLAlchemyError:
        return JSONResponse({"message": "Database failure", "code": "1"}, status_code=404)

    return JSONResponse({"message": "success"}, status_code=201)

@app.route("/users/login", methods=["POST"])
@requires("authenticated")
async def login_user(request):
    # TODO: oauth2-jwt: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
    #                   Is data signed?
    try:
        session = Session()
        token = session.query(Tokens).filter_by(idUser=request.user.id).one_or_none()
        session.commit()
    except exc.SQLAlchemyError:
        return JSONResponse({"message": "Database failure", "code": "1"}, status_code=404)

    if not token:
        try:
            session = Session()
            token = Tokens(
                idUser = request.user.id,
            )
            session.add(token)
            session.commit()
        except exc.SQLAlchemyError:
            return JSONResponse({"message": "Failed to generate token", "code": "1"}, status_code=409)

    response = JSONResponse({"message": "success"}, status_code=201)
    response.set_cookie(
        key="token",
        value=token.token,
        max_age=300,
        path="/",
        secure=True, # assert it's only valid through SSL/HTTPS
        samesite="strict",
        )
    return response

@app.route("/users/logout", methods=["GET"])
@requires("authenticated")
async def logout_user(request):
    response = JSONResponse({"message": "success"}, status_code=200)
    response.delete_cookie(key="token", path="/")

    try:
        session = Session()
        session.query(Tokens).filter_by(idUser=request.user.id).delete()
        session.commit()
    except exc.SQLAlchemyError:
        return JSONResponse({"message": "Failed to logout", "code": "1"}, status_code=404)

    return response

class BasicAuth(BaseBasicAuth):
    # See https://pypi.org/project/starlette-auth-toolkit/
    #     http://lovelysystems.github.io/lovely.microblog/be_authentication.html
    async def find_user(self, username: str):
        try:
            session = Session()
            user = session.query(Users).filter_by(username=username).one_or_none()
            session.commit()
        except exc.SQLAlchemyError:
            return JSONResponse({"message": "Database failure", "code": "1"}, status_code=404)

        return user

    async def verify_password(self, user: Users, password: str):
        if user is None:
            return None
        if len(password) == 0:
            return None
        # Password are hashed to avoid problems after database leak.
        return hasher.verify_sync(password, user.password)

class TokenAuth(AuthenticationBackend):
    async def authenticate(self, request):
        #print (request.cookies) #.get("token")
        inputToken = request.cookies.get("token")
        if inputToken is None:
            return None

        try:
            session = Session()
            token = session.query(Tokens).filter_by(token=inputToken).one_or_none()
            session.commit()
        except exc.SQLAlchemyError:
            return JSONResponse({"message": "Database failure", "code": "1"}, status_code=404)

        if token is None:
            return None

        return AuthCredentials(["authenticated"]), token.user


#class TokenAuth(BaseTokenAuth):
#
#    async def verify(self, token: str):
#        print ("TokenAuth verify")
#        # In practice, request the database to find the token object
#        # associated to `token`, and return its associated user.
#        session = Session()
#        token = session.query(Tokens).filter_by().one_or_none()
#        session.commit()
#        print ("User", token.user.id)
#        if token:
#            return token.user
#
#        return None

app.add_middleware(
    AuthenticationMiddleware,
    # Tokens are to avoid to resend login/pass everytime.
    # TokenAuth::verify is never called. BaseTokenAuth does not work?
    #backend=BasicAuth(),
    #backend=TokenAuth(),
    backend=MultiAuth([TokenAuth(), BasicAuth()]),
    on_error=lambda _, exc: PlainTextResponse(str(exc), status_code=401),
)

################################################################################
### SSL
#
# uvicorn: https://www.uvicorn.org/deployment/#running-with-https
# mkcert: https://kifarunix.com/how-to-create-self-signed-ssl-certificate-with-mkcert-on-ubuntu-18-04/
#
################################################################################
app.add_middleware(HTTPSRedirectMiddleware) # again Man-in-the-Middle
