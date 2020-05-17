# README #

### What is this repository for? ###

This application is a minimalist RESTFUL server:

- using starlette
- using sqlalchemy as ORB
- supporting authentification based on basic and token

### How do I get set up? ###

- clone
- to run server:
    uvicorn apirest:app --port 5000 --ssl-keyfile=./example.com+4-key.pem --ssl-certfile=./example.com+4.pem
- Dependencies
    - starlette
    - sqlalchemy
    - starlette_auth_toolkit
    - uvicorn, hypercorn, etc. (Tested only with uvicorn)
- Database configuration
    any database (Tested only with mariadb10)
- How to run tests
    run script/test
- Deployment instructions
    TODO

### What's next? ###

Some ideas/personal questions:

- are credentials safe?
- Is "starlette.testclient" worth? Better than curl/bash tests?
- Is sqlalchemy worth?

### Contribution guidelines ###

- Writing tests
    TODO
- Code review
    TODO
- Other guidelines
    TODO

### Who do I talk to? ###

- Repo owner or admin
