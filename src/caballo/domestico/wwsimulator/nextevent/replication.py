from typing import Iterable
from src.caballo.domestico.wwsimulator.nextevent.simulation import Simulation, SimulationFactory


class ReplicatedSimulation(Simulation):
    """
    A replicated simulation runs different replicas using the 
    final prng state of the previous replica as the initial state of
    the next one.
    """
    def __init__(self, replicas=1, initial_seed=-1):
        self.replicas = replicas
        self.initial_seed = initial_seed


class ReplicatedSimulationFactory(SimulationFactory):
    def replicate(self, prototype: Simulation, initial_seed) -> Simulation:
        replica = 
