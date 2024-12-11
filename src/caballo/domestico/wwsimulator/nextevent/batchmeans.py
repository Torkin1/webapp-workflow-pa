from caballo.domestico.wwsimulator.nextevent.simulation import Simulation, SimulationFactory
from caballo.domestico.wwsimulator.nextevent.handlers import HandleArrival
from pdsteele.des import rngs

class BatchMeansSimulation(Simulation):
    """
    A batch means simulation runs a single simulation for a long time and
    divides the simulation time into batches.
    For each batch, the simulation collects statistics and computes the statistics.
    """
    def __init__(self, initial_seed):
        self.initial_seed = initial_seed


    def run_sim(self):
        simulation_factory = SimulationFactory()
        simulation = simulation_factory.create(self.initial_seed)
        simulation.run()

if __name__ == "__main__":
    bms = BatchMeansSimulation(1234)
    bms.run_sim()