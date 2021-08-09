# Emotional assets MVP

Backend + frontend in python


. Install python >3.9 via venv for example
. Install dependencies in requirements file `pup install -r requirements.txt`
. Start application with 

[bash]
----
uvicorn api.main:app --reload
----


## Understanding the repo organization

NOTE: It will probably change. Possibly grouping by bounded context, since it will be easier to split into microservices

We divide the packages in:

* Domain: subdivided in entity and use case. And those by bounded context
* Infrastructure

----
emo
├── __init__.py
├── domain
│   ├── entity
│   │   ├── asset
│   │   │   ├── asset.py
│   │   │   ├── asset_repository.py
│   │   │   └── condition_to_live.py
│   │   └── transfer
│   │       ├── transfer.py
│   │       └── transfer_repository.py
│   └── usecase
│       ├── asset
│       │   ├── create_asset.py
│       │   └── events.py
│       └── transfer
│           ├── delete_transfer.py
│           ├── events.py
│           ├── note_to_future_self.py
│           └── time_capsule.py
├── infrastructure
│   └── routers
│       ├── api.py
│       └── endpoints
│           ├── assets.py
│           ├── transfers.py
│           └── users.py
├── main.py
├── schemas  ## IT WILL CHANGE and be included in infrastructure
│   ├── asset.py
│   ├── json_links.py
│   ├── msg.py
│   ├── token.py
│   ├── transfer.py
│   └── user.py
├── settings.py
└── shared
    └── domain
        └── usecase
            └── validations.py

----

## Resources

https://github.com/iktakahiro/dddpy
https://jsonapi.org/
https://pydantic-docs.helpmanual.io/usage/dataclasses/
https://sderosiaux.medium.com/cqrs-what-why-how-945543482313
https://github.com/CodelyTV/scala-ddd-example/blob/master/src/mooc/main/tv/codely/mooc/video/application/search/VideosSearcher.scala
https://medium.com/codex/clean-architecture-for-dummies-df6561d42c94
https://paulovich.net/guidelines-to-enrich-anemic-domain-models-tdd-ddd/

