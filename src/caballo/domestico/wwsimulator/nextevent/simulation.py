from abc import ABC
from caballo.domestico.wwsimulator.model import Network
from caballo.domestico.wwsimulator.nextevent.events import NextEventScheduler

class Simulation():
    """
    A simulation represents a run of the network model with a scheduler.
    """
    def __init__(self, scheduler: NextEventScheduler):
        self.scheduler = scheduler
    
    def run(self):
        while self.scheduler.has_next():
            self.scheduler.next()

class SimulationFactory(ABC):
    def create(self) -> Simulation:
        pass