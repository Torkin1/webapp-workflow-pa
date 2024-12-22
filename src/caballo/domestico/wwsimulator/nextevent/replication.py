from copy import copy
from typing import Iterable
from caballo.domestico.wwsimulator.model import Network
from caballo.domestico.wwsimulator import streams
from caballo.domestico.wwsimulator.nextevent import simulation
from caballo.domestico.wwsimulator.nextevent.events import EventHandler
from pdsteele.des import rngs
from caballo.domestico.wwsimulator.nextevent.simulation import Simulation, SimulationFactory

class ReplicatedSimulation(Simulation):
    """
    A simulation that runs multiple replicas and aggregrates their statistics.
    Caller is responsible to ensure that the simulation list passed as input
    are independent replicas (i.e. they do not share state of network, scheduler, event listeners, etc.)
    """
    def __init__(self, replicas: Iterable[Simulation]):
        if len(replicas) < 1:
            raise ValueError("At least one replica is required.")
        super().__init__(replicas[0].scheduler, replicas[0].network, replicas[0].initial_seed)
        self.replicas = replicas
        self.simulation = replicas[0]

    @property
    def simulation(self):
        return self._simulation
    
    @simulation.setter
    def simulation(self, simulation):
        self._simulation = simulation
        self.scheduler = simulation.scheduler
        self.network = simulation.network
        self.study = simulation.study

    
    def run(self):
        i = 0
        while i < len(self.replicas):
            self.simulation.run()
            # collect statistics
            for key, value in self.simulation.statistics.items():
                if (key not in self.statistics):
                    self.statistics[key] = []
                self.statistics[key].append(value) 
                
            # run replicas using final prng state of previous replica
            # as initial state of the next one to reduce overlap
            i += 1
            if i < len(self.replicas):
                rngs.selectStream(streams.DEFAULT)
                seed = rngs.getSeed()
                self.simulation = self.replicas[i]
                self.simulation.initial_seed = seed
