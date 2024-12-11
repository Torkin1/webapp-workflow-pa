import logging
import unittest

from caballo.domestico.wwsimulator.nextevent import simulation
from caballo.domestico.wwsimulator.nextevent.events import Event, EventHandler
from caballo.domestico.wwsimulator.nextevent.simulation import NextEventScheduler, Simulation, SimulationFactory
from blist import sortedlist


class MockEventHandler(EventHandler):
    def _handle(self, context):
        print("Handling event of type %s", type(context.event));

class EventA(Event):
    def __init__(self, time: float, handler: EventHandler):
        super().__init__(time, handler)

class EventB(Event):
    def __init__(self, time: float, handler: EventHandler):
        super().__init__(time, handler)

class TestEventObserver(unittest.TestCase):
    def test_event_observer(self):
        factory = SimulationFactory()
        simulation = factory.create()
        scheduler = simulation.scheduler
        # reset event list, should not be necessary when init event is given to factory create params.
        scheduler._event_list = sortedlist(key=lambda event: event.time)
        scheduler.schedule(EventA(0, MockEventHandler()))
        scheduler.schedule(EventB(0, MockEventHandler()))
        scheduler.subscribe(EventA, NotificationEventA())

        while scheduler.has_next():
            scheduler.next()
        
class NotificationEventA(EventHandler):
    def _handle(self, context):
        print("Received notification for event A")


if __name__ == "__main__":
    unittest.main()