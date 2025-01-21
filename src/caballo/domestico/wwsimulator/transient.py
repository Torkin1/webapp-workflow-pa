from copy import copy
from typing import Iterable
from caballo.domestico.wwsimulator.model import Network
from caballo.domestico.wwsimulator import streams
from caballo.domestico.wwsimulator import simulation
from caballo.domestico.wwsimulator.events import EventHandler
from pdsteele.des import rngs
from caballo.domestico.wwsimulator.simulation import Simulation, SimulationFactory

class TransientSimulation(Simulation):

    def __init__(self, replica: Simulation):
        super().__init__(replica.scheduler, replica.network, replica.initial_seed)
        self.simulation = replica

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
        self.simulation.run()
        # collect statistics
        for key, value in self.simulation.statistics.items():
            if (key not in self.statistics):
                self.statistics[key] = []
            self.statistics[key].append(value) 
        # new
        for key, value in self.simulation.sample.items():
            if (key not in self.sample):
                self.sample[key] = []
            self.sample[key].append(value) 