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


Create now a file named `.env` inside the kpm folder containing at least the following values:

```
# Generate with 
# openssl rand -hex 32
JWT_SECRET_KEY=

# If needed
EMAIL_SENDER_ADDRESS=
EMAIL_SENDER_PASSWORD=
EMAIL_SMTP_SERVER=mail.8vi.cat

ASSET_S3_BUCKE=kpm-dev
ASSET_S3_ACCESS=
ASSET_S3_SECRET= 


# Generate it with python 
# import base64
# from Crypto.Random import get_random_bytes
# kek_bytes = get_random_bytes(32)
# kek = base64.b64encode(kek_bytes).decode('utf-8')
# print("DATA_KEY_ENCRYPTION_KEY=", kek)
DATA_KEY_ENCRYPTION_KEY=
```

**NOTE**: If you are running the tests in windows, you might need to set-up those 
as environment variables. 

## 🗄️ Understanding the repo organization


We divide the packages in:
* Bounded context
  * Adapters (Contains databases, views, publishers, notifications code...)
    * memoryDatabase
  * Domain
  * entrypoints (it has implementations with the frameworks)
    * fastAPI
  * service_layer (command and event handlers)


````
emo
├── main.py
├── settings.py
├── assets
│   ├── adapters  # Contains databases, views, publishers, notifications code...
│   │   ├── filestorage
│   │   │   └── ....py
│   │   └── memrepo
│   │       └── ....py
│   ├── domain  # Domain logic
│   │   ├── commands.py
│   │   ├── events.py
│   │   ├── model.py
│   │   └── repositories.py  # Abstract interfaces
│   ├── entrypoints
│   │   ├── redis_eventconsumer # Example
│   │   └── fastapi
│   │       ├── schema_utils.py
│   │       └── schemas.py
│   └── service_layer  # Reactions to commands and events
│       ├── schema_utils.py
│       └── schemas.py
├── shared
│   ├── adapters
│   ├── domain
│   ├── entrypoints
│   └── service_layer
│       ├── message_bus.py
│       └── unit_of_work.py
└── users
    ├── adapters
    ├── domain
    ├── entrypoints
    └── service_layer
````

## 🧪✅ Testing and code cleaning

* Run all pre-commit steps: `make precommit`
* Run tests calling `make test`
* Format code with `make format`
* Lint code with `make lint`

NOTE: clean python cache via `make clean` if needed

### Domain Driven Design 

> **Anemic Classes**
> 
>It’s the photograph of a poor implemented business requirements. This kind of classes only store data, they do not implement behaviors or policies. These code smells alone doesn’t mean that the code is bad at all. In certain conditions these characteristics are necessary. The problem happens when multiple code smells are combined in a single code base, then the software gets harder to change, the regression tests are required for small changes and the bugs are frequent.
>
> -- From https://paulovich.net/guidelines-to-enrich-anemic-domain-models-tdd-ddd/

Each `AggregateRoot` has its own `AbstractRepository`.
And each `AbstractRepository` has its own `UnitOfWork`

Since we are using messaging patterns, in the service layer we will have
the handlers for each event or command. Ideally, those have only one repo
and communicate with eachother via events. 

## WRITING FASTAPI 
### Background tasks
| :boom: DANGER              |
|:---------------------------|
|In prod, it seems like two background tasks do not run at the same time so try to unify them.|

E.g. with one handler send an email and with another handler send another email.
The second background task is not sent. 


### Responses
| :boom: DANGER              |
|:---------------------------|
|Never use the `response_model` parameter when defining the endpoint **AND** using a pydantic model as return.|

**DON'T** DO:

```python
@router.get("", response_model=List[UserResponse]

})
async

def get_all_users(repo: UserRepository = Depends(user_repository)):
  return [to_pydantic_model(u, UserResponse) for u in repo.all_assets()]
```
If you do it, it will execute twice all the validators you might have defined in your
model, causing unexpected behaviour. (see https://stackoverflow.com/a/69104403/5375579)

**DO**

```python
@router.get("", responses={
  status.HTTP_200_OK: {"model": List[UserResponse]}
})
async def get_all_users(repo: UserRepository = Depends(user_repository)):
  return [to_pydantic_model(u, UserResponse) for u in repo.all_assets()]
```

|:warning: ALERT|
|:--------------|
|`POST` and `PUT` endpoints should never return data. If needed, just redirect to the `GET` endpoint with the corresponding HTTP code (201, 202, 203...). This is to respect Command Query Segregation principle (command ONLY modifies state and Query ONLY answers questions)|
|**EXCEPTION**: login to obtain token|


## 📧 E-mail service

Sending an email takes time. 
Due to this we execute it async using fastapi background tasks as of now
But see `shared/adapters/notifications` and `shared/entrypoints/fastapi/dependencies.py`

## 🗃️ MongoDB 

Some integration tests require a mongoDB running. 
And to support transactions, it requires some extra configuration (replica set).

Update your `mongod.cfg` with the following

```yaml
replication:
  oplogSizeMB: 2000
  replSetName: rs0
  enableMajorityReadConcern: false
```

start your mongod with 

```shell
mongod --port 27017 --replSet rs0 --bind_ip localhost
```

Then, in another terminal execute `mongosh` (or `mongo.exe`) 
and use `rs.initiate()` to initiate a new replica set.
If you get some errors like not finding the config file or replica set not configured,
in the `mongosh` terminal execute: 

```shell
cfg = { _id:"rs0", members: [{ _id:0,host:"kpm_mongo:27017"}] };

rs.initiate(cfg)
```

See:

* https://docs.mongodb.com/manual/tutorial/convert-standalone-to-replica-set/
* 


Extra for future

* pymongo docs https://pymongo.readthedocs.io/en/stable/api/pymongo/
* Capped Collections (for events): https://docs.mongodb.com/manual/core/capped-collections/
* Authentication https://docs.mongodb.com/manual/tutorial/configure-scram-client-authentication/

## 🔘️ TODOs

* [ ] Investigate why in prod fastapi dows not handle well multiple background tasks
* Database
  * [X] change database to a persistent one
  * [ ] Schema evolution in database and dataclasses. How to do it?
  * [ ] Test all views and databases in the same setup
* [ ] Clean DomainID mess. Pass it to UUID or string and use type class
* [ ] Add error translations


Low prio:
* [X] Improve loggers https://stackoverflow.com/a/64807716/5375579 + custom json schemas
* [ ] Create flake8 rule to ensure domain does not have any dependencies on INF
* [ ] flake8 rules to forbid cross-bounded context dependencies



## 📚 Resources

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