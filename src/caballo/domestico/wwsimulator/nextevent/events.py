from abc import abstractmethod
from typing import Callable

from caballo.domestico.wwsimulator.model import Job, Network, Server
from caballo.domestico.wwsimulator.nextevent.events import Event

class EventContext():

    def __init__(self, event: Event, network: Network):
        self.event = event
        self.network = network

class EventHandler(Callable):
    def __init__(self):
        pass

    @abstractmethod
    def _handle(self, context: EventContext):
        pass

    def __call__(self, context: EventContext):
        self._handle(context)

class Event():
    """
    An event occurs at a specific simulation time and can change the simulation state.
    The exact effect of an event on the state is determined by the handler function.
    """
    def __init__(self, time: float, handler: EventHandler):
        self.time = time
        self.handler = handler

class JobMovementEvent(Event):
    """
    A job can move from one node of the network to another.
    """
    def __init__(self, time: float, handler: EventHandler, job: Job, server: Server):
        super().__init__(time, handler)
        self._job = job
        self._server = server

class ArrivalEvent(JobMovementEvent):
    def __init__(self, time: float, handler: EventHandler, job: Job, server: Server):
        super().__init__(time, handler, job, server)

class DepartureEvent(JobMovementEvent):
    def __init__(self, time: float, handler: EventHandler, job: Job, server: Server):
        super().__init__(time, handler, job, server)
