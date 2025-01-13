from caballo.domestico.wwsimulator.events import ArrivalEvent, DepartureEvent, JobMovementEvent
from caballo.domestico.wwsimulator.handlers import ArrivalsGeneratorSubscriber, HandleFirstArrival
from caballo.domestico.wwsimulator.output import InterarrivalTimeEstimator, ServiceTimeEstimator, ThroughputEstimator, ResponseTimeEstimator, PopulationEstimator
from caballo.domestico.wwsimulator.replication import ReplicatedSimulation
from caballo.domestico.wwsimulator.batchmeans import BatchMeansInterceptor, BatchMeansSimulation
from caballo.domestico.wwsimulator import SIMULATION_FACTORY_CONFIG_PATH

from caballo.domestico.wwsimulator.simulation import SimulationFactory
import json

SEED = int("5E1BE110", 16) # :-*

def subscribe_estimators(simulation):
    simulation.scheduler.subscribe(DepartureEvent, ThroughputEstimator())
    simulation.scheduler.subscribe(JobMovementEvent, ResponseTimeEstimator())
    simulation.scheduler.subscribe(JobMovementEvent, PopulationEstimator())
    simulation.scheduler.subscribe(ArrivalEvent, InterarrivalTimeEstimator())
    simulation.scheduler.subscribe(DepartureEvent, ServiceTimeEstimator())
     

def bm_main(experiment, lambda_val, seed):
    batch_size = experiment['batch_means']['batch_size']
    batch_num = experiment['batch_means']['batch_num']
    num_arrivals = batch_size * batch_num
    factory = SimulationFactory()

    simulation = factory.create(HandleFirstArrival(), experiment, lambda_val, seed=seed)
    bm_simulation = BatchMeansSimulation(simulation)

    simulation.scheduler.subscribe(ArrivalEvent, ArrivalsGeneratorSubscriber(num_arrivals))
    subscribe_estimators(simulation)
    
    simulation.scheduler.intercept(DepartureEvent, BatchMeansInterceptor(batch_size, batch_num, bm_simulation))

    bm_simulation.run()
    bm_simulation.print_statistics()

def rep_main(experiment, lambda_val, seed):
    replicas = []
    factory = SimulationFactory()
    num_arrivals = experiment['batch_means']['batch_size']
    num_replicas = experiment['batch_means']['batch_num']
    for _ in range(num_replicas):
        replica = factory.create(HandleFirstArrival(), experiment, lambda_val, seed=seed)
        replica.scheduler.subscribe(ArrivalEvent, ArrivalsGeneratorSubscriber(num_arrivals))
        subscribe_estimators(replica)
        replicas.append(replica)
    simulation = ReplicatedSimulation(replicas)
    simulation.run()
    simulation.print_statistics()


if __name__ == "__main__":
    with open(SIMULATION_FACTORY_CONFIG_PATH, 'r') as file:
        data = json.load(file)
    for experiment in data['exps']:
        # replicated simulation
        # rep_main(experiment)
        # batch means simulation
        for lambda_val in experiment['arrival_distr']['params']:
             print("lambda_val: ", lambda_val)
             bm_main(experiment, lambda_val, SEED)
             #rep_main(experiment, lambda_val, SEED)




