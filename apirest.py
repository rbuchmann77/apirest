# -*- coding: utf-8 -*-
################################################################################
###
### Quick start
### -----------
### script/test
###
###
### NO SSL
### ------
### curl -i http://localhost:8000/friends
###
###
### General info on authentication/authorization
### --------------------------------------------
### - https://blog.restcase.com/4-most-used-rest-api-authentication-methods/
### - https://blog.octo.com/securiser-une-api-rest-tout-ce-quil-faut-savoir/
###
###
### Traps
### -----
### Starlette's examples do not work together:
### - database examples are using sqlite only.
### - authentication examples are incomplete.
### - starlette.orm and sqlalchemy are differents.
###
### starlette_auth_toolkit sounds nice but... BasicTokenAuth does not work at all.
### oauth2-jwt is for fastapi. Seems to be incompatible against starlette.
###
### flama project is incomplete.
###
### oauth2 is not trivial. Hard to make it when learning python in the same time.
###
################################################################################

# orb
from repositories import engine, Friends, Session
#from sqlalchemy.orm import joinedload
from datetime import date
from sqlalchemy import exc

# basic server
from starlette.applications import Starlette
from starlette.responses import JSONResponse

# auth
from starlette.authentication import requires

app = Starlette(
    on_startup=[engine.connect],
    on_shutdown=[engine.dispose]
)

import authHandling # noqa: W402

@app.route("/", methods=["GET"])
async def home(request):
    return JSONResponse({"message": "OK"}, status_code=201)

@app.route('/friends', methods=["GET"])
@requires("authenticated")
async def list_friends(request):
    # The following code works... and useless since it's already fetched, magically.
    #     session = Session()
    #     user = session.query(Users).options(joinedload(Users.friends)).filter_by(username=request.user.username).one()
    #     session.commit()
    #
    content = [
        {
            "name": myFriend.name,
        }
        for myFriend in request.user.friends
    ]
    return JSONResponse(content)

@app.route('/friends', methods=["POST"])
@requires("authenticated")
async def add_friends(request):
    data = await request.json()
    year, month, day = data["birthdate"].split('-')
    birthdate = date(int(year), int(month), int(day))
    newFriend = Friends(
        name=data["name"],
        genre=data["genre"],
        birthdate=birthdate,
        idUser=request.user.id,
    )

    try:
        session = Session()
        session.add(newFriend)
        session.commit()
    except exc.SQLAlchemyError:
        return JSONResponse({"message": "name already used", "code": "1"}, status_code=409)

    return JSONResponse({
        "id":newFriend.id,
        "name":newFriend.name,
        "genre":newFriend.genre,
        "birthdate":data["birthdate"], #newFriend.birthdate.format("%y-%m-%d"),
        "idUser":newFriend.idUser,
    })


@app.route("/friends/{name:str}", methods=["DELETE"])
@requires("authenticated")
async def del_friends(request):
    #for myFriend in request.user.friends:
    #    if myFriend.name == request.path_params['name']:
    #        del myFriend # ORM should clean up the database but it does not work as intended.
    #        return JSONResponse({"message": "delete completed", "code": "0"})
    #return JSONResponse({"message": "friend not found", "code": "1"}, status_code=404)
    try:
        session = Session()
        session.query(Friends).filter_by(idUser=request.user.id,name=request.path_params['name']).delete()
        session.commit()
    except exc.SQLAlchemyError:
        return JSONResponse({"message": "friend does not exist", "code": "1"}, status_code=404)

    return JSONResponse({"message": "delete completed", "code": "0"})

################################################################################
### autorun
################################################################################

#if __name__ == "__main__":
#    uvicorn.run("apirest:app", host="127.0.0.1", port=5000, log_level="info") # not SSL. To fix?
