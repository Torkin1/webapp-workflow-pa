from abc import ABC, abstractmethod

from blist import sortedlist

from caballo.domestico.wwsimulator.model import Network
from caballo.domestico.wwsimulator.nextevent.events import (Event, EventContext,
                                                            EventHandler,
                                                            )
from pdsteele.des import rngs


class Simulation():
    """
    A simulation represents a run of the network model with a scheduler.
    """
    def __init__(self, network: Network, initial_seed: int):
        
        self.network = network

        self.scheduler = NextEventScheduler(self)
        """
        The scheduler that manages the simulation events.
        """
        self.initial_seed = initial_seed
        """
        Initial value for the prng streams.
        """
        self.statistics = {}
        """
        A dictionary of statistics collected during the simulation run.
        type: Dict[str, Iterable[float]]
        key: statistic name
        value: a list of values (one value if single run, multiple values if replicated/batched run)
        """
    
    def run(self):
        # init prng streams with initial seed
        rngs.plantSeeds(self.initial_seed)
        # consume events until the scheduler has no more events
        while self.scheduler.has_next():
            self.scheduler.next()

class SimulationFactory():
    """
    factory for creating simulations.
    """
    def create(self, network: Network, init_event_handler: EventHandler, seed=rngs.DEFAULT) -> Simulation:
        
        # rule out random and user input values for seed
        if seed < 0:
            raise ValueError("Seed must be a positive integer")
        
        # builds the simulation
        simulation = Simulation(network, initial_seed=seed)
        simulation.scheduler.schedule(Event(0, init_event_handler))
        simulation.initial_seed = seed

        return simulation
        
class NextEventScheduler:
    def __init__(self, simulation: Simulation):
        self._event_list = sortedlist(key=lambda event: event.time)
        self._simulation = simulation
        self.stop=False
    
    def has_next(self) -> bool:
        """
        Return true if there are more events to process.
        """
        return not self.stop and len(self._event_list) > 0
    
    def next(self):
        """
        Consumes the event with the earliest scheduled time in the event list
        and calls the event handler.
        """
        if len(self._event_list) == 0:
            raise ValueError("No more events to process.")
        event = self._event_list.pop(0)
        context = EventContext(event, self._simulation.network, self, self._simulation.statistics)
        event.handle(context)

    def schedule(self, event: Event, delay: float=0.0):
        """
        Adds the event to the event list with an optional delay
        added to its scheduling time.
        """
        event.time += delay
        self._event_list.add(event)
