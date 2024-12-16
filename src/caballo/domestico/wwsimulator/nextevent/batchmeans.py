from caballo.domestico.wwsimulator.nextevent.simulation import Simulation, SimulationFactory
from caballo.domestico.wwsimulator.nextevent.handlers import HandleFirstArrival, EventHandler
from caballo.domestico.wwsimulator.nextevent.events import DepartureEvent
from caballo.domestico.wwsimulator.output import ThroughputEstimator
from pdsteele.des import rngs

class BatchMeansSimulation(Simulation):
    """
    A batch means simulation runs a single simulation for a long time and
    divides the simulation time into batches.
    For each batch, the simulation collects statistics and computes the statistics.
    """
    def __init__(self, initial_seed, init_event_handler):
        self.initial_seed = initial_seed
        self.init_event_handler = init_event_handler


    def run(self):
        simulation_factory = SimulationFactory()
        simulation = simulation_factory.create(self.init_event_handler, self.initial_seed)
        simulation.scheduler.subscribe(DepartureEvent, BatchMeansSub())
        simulation.scheduler.subscribe(DepartureEvent, ThroughputEstimator())
        simulation.run()

class BatchMeansSub(EventHandler):
    """
    Subscribes to job completions only
    """
    def __init__(self):
        super().__init__()
        self.job_num = 0
        self.batch_num = 0
    
    def _handle(self, context):
        self.job_num += 1
        if self.job_num % 10 == 0:
            print(f"Throughtput: {context.statistics}")

if __name__ == "__main__":
    bms = BatchMeansSimulation(1234, HandleFirstArrival())
    bms.run()