from caballo.domestico.wwsimulator.nextevent.simulation import Simulation, SimulationFactory
from caballo.domestico.wwsimulator.nextevent.handlers import HandleFirstArrival, EventHandler
from caballo.domestico.wwsimulator.nextevent.events import DepartureEvent
from caballo.domestico.wwsimulator.nextevent.output import ThroughputEstimator
from pdsteele.des import rngs
import json
from caballo.domestico.wwsimulator import SIMULATION_FACTORY_CONFIG_PATH

class BatchMeansSimulation(Simulation):
    """
    A batch means simulation runs a single simulation for a long time and
    divides the simulation time into batches.
    For each batch, the simulation collects statistics and computes the statistics.
    """
    def __init__(self, initial_seed, init_event_handler):
        self.initial_seed = initial_seed
        self.init_event_handler = init_event_handler
    
    def get_params(self):
        with open(SIMULATION_FACTORY_CONFIG_PATH, 'r') as file:
            data = json.load(file)
        for experiment in data['exps']:
            batch_num = experiment['batch_means']['batch_num']
            batch_size = experiment['batch_means']['batch_size']
            return batch_num, batch_size

    def run(self):
        simulation_factory = SimulationFactory()
        simulation = simulation_factory.create(self.init_event_handler, self.initial_seed)
        batch_num, batch_size = self.get_params()
        simulation.scheduler.subscribe(DepartureEvent, BatchMeansSub(batch_size, batch_num))
        simulation.scheduler.subscribe(DepartureEvent, ThroughputEstimator())
        simulation.run()

class BatchMeansSub(EventHandler):
    """
    Subscribes to job completions only
    """
    def __init__(self, batch_size:int, batch_num:int):
        super().__init__()
        self.job_completed = 0
        """
        Numero di job usciti dal sistema
        """
        self.batch_completed = 0
        """
        Numero di batch completati
        """
        self.batch_size = batch_size
        """
        Taglia del batch
        """
        self.batch_num = batch_num
        """
        Numero di batch totali
        """
        self.batch_statistics = {}
    
    def _handle(self, context):
        # conteggio job che escono dal sistema
        if context.event.external:
            self.job_completed += 1

        # ogni batch_size job completati, esegue il flush delle statistiche
        if self.job_completed == self.batch_size:
            self.job_completed = 0
            self.batch_completed += 1
            for key in context.statistics:
                if key not in self.batch_statistics:
                    self.batch_statistics[key] = []
                self.batch_statistics[key].append(context.statistics[key])
            context.statistics = {}
            print(f"Throughtput: {self.batch_statistics} with index {self.batch_completed}")
            
        if self.batch_completed == self.batch_num:
            print("Batch means completed")
            # TODO: schedualare evento di stop


if __name__ == "__main__":
    bms = BatchMeansSimulation(1234, HandleFirstArrival())
    bms.run()
