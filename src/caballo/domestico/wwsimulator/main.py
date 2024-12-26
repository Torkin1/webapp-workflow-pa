from caballo.domestico.wwsimulator.nextevent.events import ArrivalEvent, DepartureEvent, Event, EventHandler
from caballo.domestico.wwsimulator.nextevent.handlers import ArrivalsGeneratorSubscriber, HandleFirstArrival
from caballo.domestico.wwsimulator.nextevent.output import ThroughputEstimator
from caballo.domestico.wwsimulator.nextevent.replication import ReplicatedSimulation
from caballo.domestico.wwsimulator.nextevent.batchmeans import BatchMeansSub, BatchMeansSimulation
from caballo.domestico.wwsimulator import SIMULATION_FACTORY_CONFIG_PATH

from caballo.domestico.wwsimulator.nextevent.simulation import SimulationFactory
import json

if __name__ == "__main__":
    NUM_ARRIVALS = 10
    NUM_REPLICAS = 10
    with open(SIMULATION_FACTORY_CONFIG_PATH, 'r') as file:
        data = json.load(file)
    for experiment in data['exps']:
        factory = SimulationFactory()

        # replicated simulation
        replicas = []
        for i in range(NUM_REPLICAS):
            replica = factory.create(HandleFirstArrival(), experiment)
            replica.scheduler.subscribe(ArrivalEvent, ArrivalsGeneratorSubscriber(NUM_ARRIVALS))
            replica.scheduler.subscribe(DepartureEvent, ThroughputEstimator())
            replicas.append(replica)
        simulation = ReplicatedSimulation(replicas)
        simulation.run()
        simulation.print_statistics()

        # batch means simulation
        batch_size = experiment['batch_means']['batch_size']
        batch_num = experiment['batch_means']['batch_num']
        NUM_ARRIVALS = batch_size * batch_num

        simulation = factory.create(HandleFirstArrival(), experiment)
        bm_simulation = BatchMeansSimulation(simulation)

        simulation.scheduler.subscribe(DepartureEvent, BatchMeansSub(batch_size, batch_num, bm_simulation))
        simulation.scheduler.subscribe(ArrivalEvent, ArrivalsGeneratorSubscriber(NUM_ARRIVALS))
        simulation.scheduler.subscribe(DepartureEvent, ThroughputEstimator())

        bm_simulation.run()
        bm_simulation.print_statistics()
