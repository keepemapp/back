# Emotional assets MVP

Backend + frontend in python


1. Install python >3.9 via venv for example. If you have done it via venv, to activate the environment do `source venv/bin/activate`
2. Install dependencies in requirements file `pip install -r requirements.txt`
3. Create `data` folder in parent repository. Temporarily used to store the data
4. Start application with 


````bash
uvicorn emo.main:app --reload
````

## Understanding the repo organization


We divide the packages in:
* Bounded context
  * Domain
     * entity
     * use case (including domain events)
  * Infrastructure (it has implementations with the frameworks)
    * fastAPI
    * memoryDatabase
    * ...

````
emo
├── main.py
├── settings.py
├── shared
│   ├── domain
│   │   └── usecase
│   │       ├── event.py
│   │       └── validations.py
│   ├── infrastructure
│   │   └── fastapi
│   │       ├── schema_utils.py
│   │       └── schemas.py
│   └── security.py
├── assets
│   ├── domain
│   └── infrastructure
└── users
    ├── domain
    │   ├── entity
    │   │   ├── user_repository.py
    │   │   └── users.py
    │   └── usecase
    │       ├── change_user_password.py
    │       ├── exceptions.py
    │       ├── query_user.py
    │       └── register_user.py
    └── infrastructure
        ├── dependencies.py
        ├── fastapi
        │   └── v1
        │       ├── schemas
        │       │   ├── token.py
        │       │   └── users.py
        │       ├── token.py
        │       └── users.py
        └── memory
            ├── message_bus.py
            └── repository.py
````

## Testing and code cleaning

* Run tests calling `pytest`
* Format code with `black emo`
* Lint code with `flake8 emo tests`

NOTE: clean python cache via `py3clean emo tests` if needed

## Resources

* https://github.com/iktakahiro/dddpy
* https://softwareengineering.stackexchange.com/questions/396151/which-layer-do-ddd-repositories-belong-to
* https://jsonapi.org/
* https://pydantic-docs.helpmanual.io/usage/dataclasses/
* https://sderosiaux.medium.com/cqrs-what-why-how-945543482313
* https://github.com/CodelyTV/scala-ddd-example/blob/master/src/mooc/main/tv/codely/mooc/video/application/search/VideosSearcher.scala
* https://medium.com/codex/clean-architecture-for-dummies-df6561d42c94
* https://paulovich.net/guidelines-to-enrich-anemic-domain-models-tdd-ddd/

