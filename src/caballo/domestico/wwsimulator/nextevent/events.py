from abc import abstractmethod
from typing import Any, Callable
from blist import sortedlist
from caballo.domestico.wwsimulator.model import Job, Network, Server, Queue, Node, State


class EventContext():

    def __init__(self, event, network: Network, scheduler):
        self.event = event
        self.network = network
        self.scheduler = scheduler

class EventHandler(Callable):
    def __init__(self):
        # unused constructor
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
        self.handle = handler

class JobMovementEvent(Event):
    """
    A job can move from one node of the network to another.
    """
    def __init__(self, time: float, handler: EventHandler, job: Job, server: Server):
        super().__init__(time, handler)
        self.job = job
        self.server = server

# nell'arrival il server è quello in cui sta arrivando il job
class ArrivalEvent(JobMovementEvent):
    def __init__(self, time: float, handler: EventHandler, job: Job, server: Server):
        super().__init__(time, handler, job, server)

# nella departure il server è quello da cui sta partendo il job
class DepartureEvent(JobMovementEvent):
    def __init__(self, time: float, handler: EventHandler, job: Job, server: Server):
        super().__init__(time, handler, job, server)

class NextEventScheduler:
    def __init__(self, network: Network):
        self._event_list = sortedlist(key=lambda event: event.time)
        self._network = network
    
    @property
    def network(self):
        return self._network
    
    @network.setter
    def network(self, network):
        self._network = network
        self._event_list.clear()

    def has_next(self) -> bool:
        """
        Return true if there are more events to process.
        """
        return len(self._event_list) > 0
    
    def next(self):
        """
        Consumes the event with the earliest scheduled time in the event list
        and calls the event handler.
        """
        if len(self._event_list) == 0:
            raise ValueError("No more events to process.")
        event = self._event_list.pop(0)
        context = EventContext(event, self.network, self)
        event.handle(context)

    def schedule(self, event: Event, delay: float=0.0):
        """
        Adds the event to the event list with an optional delay
        added to its scheduling time.
        """
        event.time += delay
        self._event_list.add(event)
   