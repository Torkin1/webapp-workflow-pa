from caballo.domestico.wwsimulator.nextevent.events import ArrivalEvent, DepartureEvent, JobMovementEvent
from caballo.domestico.wwsimulator.nextevent.handlers import ArrivalsGeneratorSubscriber, HandleFirstArrival
from caballo.domestico.wwsimulator.nextevent.output import ThroughputEstimator, ResponseTimeEstimator, PopulationEstimator
from caballo.domestico.wwsimulator.nextevent.replication import ReplicatedSimulation
from caballo.domestico.wwsimulator.nextevent.batchmeans import BatchMeansSub, BatchMeansSimulation
from caballo.domestico.wwsimulator import SIMULATION_FACTORY_CONFIG_PATH

from caballo.domestico.wwsimulator.nextevent.simulation import SimulationFactory
import json
def bm_main(experiment, lambda_val):
        batch_size = experiment['batch_means']['batch_size']
        batch_num = experiment['batch_means']['batch_num']
        NUM_ARRIVALS = batch_size * batch_num
        factory = SimulationFactory()

        simulation = factory.create(HandleFirstArrival(), experiment, lambda_val)
        bm_simulation = BatchMeansSimulation(simulation)

        simulation.scheduler.subscribe(ArrivalEvent, ArrivalsGeneratorSubscriber(NUM_ARRIVALS))
        simulation.scheduler.subscribe(DepartureEvent, BatchMeansSub(batch_size, batch_num, bm_simulation))
        simulation.scheduler.subscribe(DepartureEvent, ThroughputEstimator())
        simulation.scheduler.subscribe(JobMovementEvent, ResponseTimeEstimator())
        simulation.scheduler.subscribe(JobMovementEvent, PopulationEstimator())

        bm_simulation.run()
        bm_simulation.print_statistics()

def rep_main(experiment):
    replicas = []
    factory = SimulationFactory()
    for _ in range(NUM_REPLICAS):
        replica = factory.create(HandleFirstArrival(), experiment)
        replica.scheduler.subscribe(ArrivalEvent, ArrivalsGeneratorSubscriber(NUM_ARRIVALS))
        replica.scheduler.subscribe(DepartureEvent, ThroughputEstimator())
        replica.scheduler.subscribe(JobMovementEvent, ResponseTimeEstimator())
        replica.scheduler.subscribe(JobMovementEvent, PopulationEstimator())
        replicas.append(replica)
    simulation = ReplicatedSimulation(replicas)
    simulation.run()
    simulation.print_statistics()


if __name__ == "__main__":
    NUM_ARRIVALS = 10
    NUM_REPLICAS = 10
    with open(SIMULATION_FACTORY_CONFIG_PATH, 'r') as file:
        data = json.load(file)
    for experiment in data['exps']:
        # replicated simulation
        # rep_main(experiment)
        # batch means simulation
        for lambda_val in experiment['arrival_distr']['params']:
             print("lambda_val: ", lambda_val)
             bm_main(experiment, lambda_val)




