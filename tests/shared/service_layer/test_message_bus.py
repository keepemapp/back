import pytest

from kpm.shared.domain.commands import Command
from kpm.shared.domain.events import Event
from kpm.shared.domain.model import RootAggregate
from kpm.shared.domain.repository import DomainRepository
from kpm.shared.service_layer import message_bus as mb
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork


class TestEvent(Event):
    pass


class Agg1(RootAggregate):
    def __hash__(self):
        return hash(self.id)

    def trigger_event(self):
        self._events.append(TestEvent())


class Agg2(RootAggregate):
    def __hash__(self):
        return hash(self.id)


class AggRepo(DomainRepository):
    def __init__(self):
        super().__init__()
        self._repo = []
        self._seen = set()

    def put(self, agg):
        self._repo.append(agg)
        self._seen.add(agg)


class AggUoW(AbstractUnitOfWork):
    def __init__(self):
        super(AggUoW, self).__init__()
        self.repo = None
        self.times_committed = 0

    def __enter__(self):
        self.committed = False
        self.repo = AggRepo()
        return super().__enter__()

    def _commit(self):
        self.repo.commit()
        self.committed = True
        self.times_committed += 1

    def rollback(self):
        pass


@pytest.mark.unit
class TestUoWs:
    def test_event_gathering(self):
        uows = mb.UoWs({Agg1: AggUoW(), Agg2: AggUoW()})
        with uows.get(Agg1) as uow:
            agg1 = Agg1()
            agg1.trigger_event()
            assert len(agg1.events) == 1
            uow.repo.put(agg1)
            uow.commit()

        assert len(uows.collect_new_events()) == 1

    def test_events_are_cleared_after_gathered(self):
        uows = mb.UoWs({Agg1: AggUoW(), Agg2: AggUoW()})
        with uows.get(Agg1) as uow:
            agg1 = Agg1()
            agg1.trigger_event()
            assert len(agg1.events) == 1
            uow.repo.put(agg1)
            uow.commit()

        _ = uows.collect_new_events()
        assert len(uows.collect_new_events()) == 0


class TestCommand(Command):
    pass


def handler(cmd_event, uow, trigger=False):
    with uow:
        agg = Agg1()
        if trigger:
            agg.trigger_event()
        uow.repo.put(agg)
        uow.commit()


@pytest.mark.unit
class TestMessageBus:
    def test_events(self):
        uow = AggUoW()
        uows = mb.UoWs({Agg1: uow})
        EVENT_HANDLERS = {TestEvent: [lambda event: handler(event, uow)]}
        COMMAND_HANDLERS = {}
        bus = mb.MessageBus(uows, EVENT_HANDLERS, COMMAND_HANDLERS)

        bus.handle(TestEvent())
        assert uow.times_committed == 1

    def test_commands(self):
        uow = AggUoW()
        uows = mb.UoWs({Agg1: uow})
        EVENT_HANDLERS = {}
        COMMAND_HANDLERS = {TestCommand: lambda event: handler(event, uow)}
        bus = mb.MessageBus(uows, EVENT_HANDLERS, COMMAND_HANDLERS)

        bus.handle(TestCommand())
        assert uow.times_committed == 1

    def test_reacts_to_generated_events(self):
        uow = AggUoW()
        uows = mb.UoWs({Agg1: uow})
        EVENT_HANDLERS = {TestEvent: [lambda event: handler(event, uow)]}
        COMMAND_HANDLERS = {
            TestCommand: lambda event: handler(event, uow, True)
        }
        bus = mb.MessageBus(uows, EVENT_HANDLERS, COMMAND_HANDLERS)

        bus.handle(TestCommand())
        assert uow.times_committed == 2
