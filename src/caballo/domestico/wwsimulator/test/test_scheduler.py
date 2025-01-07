import logging
from sched import scheduler
import unittest

from caballo.domestico.wwsimulator import simulation
from caballo.domestico.wwsimulator.events import Event, EventHandler
from caballo.domestico.wwsimulator.simulation import NextEventScheduler, Simulation, SimulationFactory
from blist import sortedlist


class MockEventHandler(EventHandler):
    def _handle(self, context):
        print("Handling event of type %s", type(context.event));

class MockInitHandler(EventHandler):
    def _handle(self, context):
        scheduler = context.scheduler
        scheduler.schedule(EventA(0, MockEventHandler()))
        scheduler.schedule(EventB(0, MockEventHandler()))
        scheduler.subscribe(EventA, NotificationEventA())

class EventA(Event):
    def __init__(self, time: float, handler: EventHandler):
        super().__init__(time, handler)

class EventB(Event):
    def __init__(self, time: float, handler: EventHandler):
        super().__init__(time, handler)

class TestEventObserver(unittest.TestCase):
    def test_event_observer(self):
        factory = SimulationFactory()
        simulation = factory.create(MockInitHandler())
        scheduler = simulation.scheduler
        while scheduler.has_next():
            scheduler.next()
        
class NotificationEventA(EventHandler):
    def _handle(self, context):
        print("Received notification for event A")


if __name__ == "__main__":
    unittest.main()