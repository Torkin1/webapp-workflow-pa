from caballo.domestico.wwsimulator.model import Network
from caballo.domestico.wwsimulator.nextevent import streams
from caballo.domestico.wwsimulator.nextevent import simulation
from caballo.domestico.wwsimulator.nextevent.events import EventHandler
from pdsteele.des import rngs
from caballo.domestico.wwsimulator.nextevent.simulation import Simulation, SimulationFactory

class ReplicatedSimulation(Simulation):
    """
    A replicated simulation runs different replicas of a prototype
    simulation using the 
    final prng state of the previous replica as the initial state of
    the next one.
    The prototype simulation is used as first replica. Subsequent replicas
    are created using the provided factory.
    """
    def __init__(self, factory: SimulationFactory, init_event_handler: EventHandler, prototype: Simulation, replicas: int):
        super().__init__(prototype.scheduler, prototype.initial_seed)
        self.replicas = replicas
        self.simulation = prototype
        self.factory = factory
        self.init_event_handler = init_event_handler
    
    def run(self):
        # run replicas using final prng state of previous replica
        # as initial state of the next one
        for i in range(self.replicas):
            self.simulation.run()
            # collect statistics
            for key, value in self.simulation.statistics.items():
                if (key not in self.statistics):
                    self.statistics[key] = []
                self.statistics[key].append(value) 
                
            # get final prng state from default stream
            rngs.selectStream(streams.DEFAULT)
            seed = rngs.getSeed()
            # create new replica
            self.simulation = self.factory.create(self.simulation.network, self.init_event_handler, seed)            

class ReplicatedSimulationFactory(SimulationFactory):
    """
    A factory for creating replicated simulations.
    """
    
    def __init__(self, factory: SimulationFactory, replicas: int):
        self.replicas = replicas
        self.factory = factory
    
    def create(self, network: Network, init_event_handler: EventHandler, seed=rngs.DEFAULT) -> ReplicatedSimulation:
        # create prototype simulation
        simulation = self.factory.create(network, init_event_handler, seed)
        return ReplicatedSimulation(self.factory, init_event_handler, simulation, self.replicas)