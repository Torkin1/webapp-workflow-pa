from caballo.domestico.wwsimulator.simulation import Simulation, SimulationFactory
from caballo.domestico.wwsimulator.handlers import HandleFirstArrival, EventHandler
from caballo.domestico.wwsimulator.events import DepartureEvent
from caballo.domestico.wwsimulator.output import ThroughputEstimator, ResponseTimeEstimator, PopulationEstimator
from pdsteele.des import rngs
import json
from caballo.domestico.wwsimulator import SIMULATION_FACTORY_CONFIG_PATH

class BatchMeansSimulation(Simulation):
    """
    A batch means simulation runs a single simulation for a long time and
    divides the simulation time into batches.
    For each batch, the simulation collects statistics and computes the statistics.
    """
    def __init__(self, simulation: Simulation):
        super().__init__(simulation.study, simulation.network, simulation.initial_seed)
        self.simulation = simulation
        self.statistics = {}

    def run(self):
        self.simulation.run()
    
    @property
    def simulation(self):
        return self._simulation
    
    @simulation.setter
    def simulation(self, simulation):
        self._simulation = simulation
        self.scheduler = simulation.scheduler
        self.network = simulation.network
        self.study = simulation.study



class BatchMeansInterceptor(EventHandler):
    """
    Intercepts job completions only.
    Must subscribe as interceptor to ensure that the statistics are flushed
    and estimators reset before they start to sample for the next batch.
    """
    def __init__(self, batch_size:int, batch_num:int, simulation:Simulation):
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
        self.simulation = simulation
    
    def _handle(self, context):
        # conteggio job che escono dal sistema
        if context.event.external:
            self.job_completed += 1
        context.new_batch = False

        # ogni batch_size job completati, esegue il flush delle statistiche
        if self.job_completed == self.batch_size:
            
            # resets resettable estimators
            scheduler = self.simulation.scheduler
            scheduler.reset_subscribers()
            
            self.job_completed = 0
            self.batch_completed += 1
            for key in context.statistics:
                if key not in self.batch_statistics:
                    self.batch_statistics[key] = []
                self.batch_statistics[key].append(context.statistics[key])
            context.statistics = {}
            # context.new_batch = True
            if self.batch_completed == self.batch_num:
                self.simulation.statistics = self.batch_statistics
                
if __name__ == "__main__":
    bms = BatchMeansSimulation(1234, HandleFirstArrival())
    bms.run()
