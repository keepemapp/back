# Emotional assets MVP

Backend + frontend in python


1. Install python >3.8 and `make` (installed by default in GNI/linux and OS X)
2. Install dependencies with `make install-dev`
3. Start application with `make run-dev`
4. Run auto-format code with `make format`
5. Run linting and tests with `make test` (see [flake8 rules](https://lintlyci.github.io/Flake8Rules/)) 
   You can see the HTML report inside `.coverage_html` folder
6. Before committing execute `make clean`


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
* https://stackoverflow.com/questions/50802874/use-case-to-command-application-layer-mapping-implementation

Extra:
* https://github.com/dannysteenman/aws-toolbox#aws-toolbox-
* https://github.com/donnemartin/system-design-primer

### Domain Driven Design 

> **Anemic Classes**
> 
>It’s the photograph of a poor implemented business requirements. This kind of classes only store data, they do not implement behaviors or policies. These code smells alone doesn’t mean that the code is bad at all. In certain conditions these characteristics are necessary. The problem happens when multiple code smells are combined in a single code base, then the software gets harder to change, the regression tests are required for small changes and the bugs are frequent.
>
> -- From https://paulovich.net/guidelines-to-enrich-anemic-domain-models-tdd-ddd/


# TODOs

* [x] Create `make` script with install, test, clean and run
* [x] Fix flake8 linting errors 
* [ ] Create flake8 rule to ensure domain does not have any dependencies on INF
* [ ] flake8 rules to forbid cross-bounded context dependencies
* [ ] Test `fastapi` users interface
* [ ] Adapt `assets` bounded context to new format