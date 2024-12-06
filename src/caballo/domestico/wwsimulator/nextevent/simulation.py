from abc import ABC, abstractmethod

from caballo.domestico.wwsimulator.model import Network
from caballo.domestico.wwsimulator.nextevent.events import (Event,
                                                            NextEventScheduler)
from pdsteele.des import rngs


class Simulation():
    """
    A simulation represents a run of the network model with a scheduler.
    """
    def __init__(self, scheduler: NextEventScheduler, initial_seed=-1):
        self.scheduler = scheduler
        self.initial_seed = initial_seed
    
    def run(self):
        # init prng streams with initial seed
        rngs.plantSeeds(self.initial_seed)
        # consume events until the scheduler has no more events
        while self.scheduler.has_next():
            self.scheduler.next()

class SimulationFactory(ABC):
    """
    Abstract factory for creating simulations.
    When implementing concrete factories, override the _create_network and _create_init_event methods
    to customize the simulation creation process.
    """
    
    # DO NOT OVERRIDE. Override other methods to modify creation behaviour.
    def create(self, seed=rngs.DEFAULT) -> Simulation:
        
        # rule out random and user input values for seed
        if seed < 0:
            raise ValueError("Seed must be a positive integer")
        
        # creates network
        network = self._create_network()

        # binds a scheduler to the network
        scheduler = NextEventScheduler(network)

        # stages the initial event
        init_event = self._create_init_event(network)
        scheduler.schedule(init_event)

        # builds the simulation
        simulation = Simulation(scheduler, initial_seed=seed)
        simulation.initial_seed = seed
        return simulation
    
    @abstractmethod
    def _create_network() -> Network:
        """
        Creates the network model and initializes its state.
        """
        pass
    
    @abstractmethod
    def _create_init_event(self, network: Network) -> Event:
        """
        Creates the initial event for the simulation.
        """
        pass
 