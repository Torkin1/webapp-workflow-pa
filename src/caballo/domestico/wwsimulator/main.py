from caballo.domestico.wwsimulator.events import ArrivalEvent, DepartureEvent, JobMovementEvent
from caballo.domestico.wwsimulator.handlers import ArrivalsGeneratorSubscriber, HandleFirstArrival
from caballo.domestico.wwsimulator.output import ThroughputEstimator, ResponseTimeEstimator, PopulationEstimator, UtilizationEstimator
from caballo.domestico.wwsimulator.replication import ReplicatedSimulation
from caballo.domestico.wwsimulator.batchmeans import BatchMeansSub, BatchMeansSimulation
from caballo.domestico.wwsimulator import SIMULATION_FACTORY_CONFIG_PATH

from caballo.domestico.wwsimulator.simulation import SimulationFactory
import json
def bm_main(experiment, lambda_val, seed):
        batch_size = experiment['batch_means']['batch_size']
        batch_num = experiment['batch_means']['batch_num']
        NUM_ARRIVALS = batch_size * batch_num
        factory = SimulationFactory()

        simulation = factory.create(HandleFirstArrival(), experiment, lambda_val, seed=seed)
        bm_simulation = BatchMeansSimulation(simulation)

        simulation.scheduler.subscribe(ArrivalEvent, ArrivalsGeneratorSubscriber(NUM_ARRIVALS))
        simulation.scheduler.subscribe(ArrivalEvent, UtilizationEstimator())
        simulation.scheduler.subscribe(DepartureEvent, BatchMeansSub(batch_size, batch_num, bm_simulation))
        simulation.scheduler.subscribe(DepartureEvent, ThroughputEstimator())
        simulation.scheduler.subscribe(JobMovementEvent, ResponseTimeEstimator())
        simulation.scheduler.subscribe(JobMovementEvent, PopulationEstimator())

        bm_simulation.run()
        bm_simulation.print_statistics()

def rep_main(experiment, lambda_val, seed):
    replicas = []
    factory = SimulationFactory()
    for _ in range(NUM_REPLICAS):
        replica = factory.create(HandleFirstArrival(), experiment, lambda_val, seed=seed)
        replica.scheduler.subscribe(ArrivalEvent, ArrivalsGeneratorSubscriber(100))
        replica.scheduler.subscribe(ArrivalEvent, UtilizationEstimator())
        replica.scheduler.subscribe(DepartureEvent, ThroughputEstimator())
        replica.scheduler.subscribe(JobMovementEvent, ResponseTimeEstimator())
        replica.scheduler.subscribe(JobMovementEvent, PopulationEstimator())
        replicas.append(replica)
    simulation = ReplicatedSimulation(replicas)
    simulation.run()
    simulation.print_statistics()


if __name__ == "__main__":
    NUM_ARRIVALS = 10
    NUM_REPLICAS = 100
    SEED = int("5E1BE110", 16) # read it upside down ...
    with open(SIMULATION_FACTORY_CONFIG_PATH, 'r') as file:
        data = json.load(file)
    for experiment in data['exps']:
        # replicated simulation
        # rep_main(experiment)
        # batch means simulation
        for lambda_val in experiment['arrival_distr']['params']:
             print("lambda_val: ", lambda_val)
             #bm_main(experiment, lambda_val, SEED)
             rep_main(experiment, lambda_val, SEED)




