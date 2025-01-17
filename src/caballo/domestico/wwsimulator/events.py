from abc import abstractmethod
from typing import Any, Callable, Dict, Iterable
from caballo.domestico.wwsimulator.model import Job, Network, Node


class EventContext():

    def __init__(self, event, network: Network, scheduler, statistics: Dict[str, Iterable[Any]]):
        self.event = event
        self.network = network
        self.scheduler = scheduler
        self.statistics = statistics
        self.new_batch = False

class EventHandler(Callable):
    def __init__(self):
        # unused constructor
        pass

    @abstractmethod
    def _handle(self, context: EventContext):
        pass

    def __call__(self, context: EventContext):
        self._handle(context)
    
    def halt_if_wrong_event(self, event_actual, event_type_expected):
        if not isinstance(event_actual, event_type_expected):
            raise ValueError(f"{self.__qualname__} can only handle {event_type_expected}, got {type(event_actual)}")

class Event():
    """
    An event occurs at a specific simulation time and can change the simulation state.
    The exact effect of an event on the state is determined by the handler function.
    """
    def __init__(self, time: float, handler: EventHandler):
        self.time = time
        self.handle = handler
        self.is_cancelled = False

class JobMovementEvent(Event):
    """
    A job can move from one node of the network to another.
    """
    def __init__(self, time: float, handler: EventHandler, job: Job, node: Node):
        super().__init__(time, handler)
        self.job = job
        self.node = node
        self.external = False
        """
        True if the job is entering/exiting the system.
        """

# nell'arrival il node è quello in cui sta arrivando il job
class ArrivalEvent(JobMovementEvent):
    def __init__(self, time: float, handler: EventHandler, job: Job, node: Node):
        super().__init__(time, handler, job, node)

# nella departure il node è quello da cui sta partendo il job
class DepartureEvent(JobMovementEvent):
    def __init__(self, time: float, handler: EventHandler, job: Job, node: Node):
        super().__init__(time, handler, job, node)

   