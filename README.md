# Emotional assets MVP


{:toc}

Backend in python


1. Install python >3.8 and `make` (installed by default in GNI/linux and OS X)
2. Install dependencies with `make install-dev`
3. Start application with `make run-dev`
4. Run auto-format code with `make format`
5. Run linting and tests with `make test` (see [flake8 rules](https://lintlyci.github.io/Flake8Rules/)) 
   You can see the HTML report inside `.coverage_html` folder
6. Before committing execute `make precommit` (runs formatting, linting, test and clean)


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
│   ├── infra
│   │   └── fastapi
│   │       ├── schema_utils.py
│   │       └── schemas.py
│   └── security.py
├── assets
│   ├── domain
│   └── infra
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
    └── infra
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

* Run all pre-commit steps: `make precommit`
* Run tests calling `make test`
* Format code with `make format`
* Lint code with `make lint`

NOTE: clean python cache via `make clean` if needed

## Resources

* https://github.com/iktakahiro/dddpy
* https://softwareengineering.stackexchange.com/questions/396151/which-layer-do-ddd-repositories-belong-to
* https://jsonapi.org/
* https://pydantic-docs.helpmanual.io/usage/dataclasses/
* https://sderosiaux.medium.com/cqrs-what-why-how-945543482313
* https://github.com/CodelyTV/scala-ddd-example/blob/master/src/mooc/main/tv/codely/mooc/video/application/search/VideosSearcher.scala
* https://medium.com/codex/clean-architecture-for-dummies-df6561d42c94
* https://paulovich.net/guidelines-to-enrich-anemic-domain-models-tdd-ddd/
* https://stackoverflow.com/questions/50802874/use-case-to-command-application-layer-mapping-implementation
* Monitoring: https://medium.com/swlh/fastapi-microservice-patterns-application-monitoring-49fcb7341d9a

Extra:
* https://github.com/dannysteenman/aws-toolbox#aws-toolbox-
* https://github.com/donnemartin/system-design-primer

### Domain Driven Design 

> **Anemic Classes**
> 
>It’s the photograph of a poor implemented business requirements. This kind of classes only store data, they do not implement behaviors or policies. These code smells alone doesn’t mean that the code is bad at all. In certain conditions these characteristics are necessary. The problem happens when multiple code smells are combined in a single code base, then the software gets harder to change, the regression tests are required for small changes and the bugs are frequent.
>
> -- From https://paulovich.net/guidelines-to-enrich-anemic-domain-models-tdd-ddd/

Each `AggregateRoot` has its own `AbstractRepository`.
And each `AbstractRepository` has its own `UnitOfWork`?

## WRITING FASTAPI endpoints

| :boom: DANGER              |
|:---------------------------|
|Never use the `response_model` parameter when defining the endpoint **AND** using a pydantic model as return.|

*DON'T** DO:
```python
@router.get("", response_model=List[UserResponse]})
async def get_all_users(repo: UserRepository = Depends(user_repository)):
    return [to_pydantic_model(u, UserResponse) for u in repo.all()]
```
If you do it, it will execute twice all the validators you might have defined in your
model, causing unexpected behaviour. (see https://stackoverflow.com/a/69104403/5375579)

**DO**
```python
@router.get("", responses={
    status.HTTP_200_OK: {"model": List[UserResponse]}
})
async def get_all_users(repo: UserRepository = Depends(user_repository)):
    return [to_pydantic_model(u, UserResponse) for u in repo.all()]
```

|:warning: ALERT|
|:--------------|
|`POST` and `PUT` endpoints should never return data. If needed, just redirect to the `GET` endpoint with the corresponding HTTP code (201, 202, 203...). This is to respect Command Query Segregation principle (command ONLY modifies state and Query ONLY answers questions)|
|EXCEPTION: login to obtain token|


# TODOs

* [ ] Ensure that we detect/register when the asset file was uploaded (or if it was), and change the response accordingly
  Either give them the publish_url or the view URL for the file when they do a `get` on the asset
* [X] Test asset file upload and retrieval
* [ ] Implement command responsibility segregation for POST APIs (do not return result and just redirect. See https://stackoverflow.com/questions/62119138/how-to-do-a-post-redirect-get-prg-in-fastapi)
  * [X] For assets
  * [ ] for Users
* [ ] Schema evolution in database and dataclasses. How to do it?
* [ ] change database to a persistent one



Low prio:
* [ ] Improve loggers https://stackoverflow.com/a/64807716/5375579 + custom json schemas
* [ ] Create flake8 rule to ensure domain does not have any dependencies on INF
* [ ] flake8 rules to forbid cross-bounded context dependencies