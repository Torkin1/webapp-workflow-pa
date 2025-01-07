import unittest

from caballo.domestico.wwsimulator.events import ArrivalEvent, DepartureEvent, Event, EventHandler
from caballo.domestico.wwsimulator.handlers import ArrivalsGeneratorSubscriber, HandleFirstArrival
from caballo.domestico.wwsimulator.output import ThroughputEstimator
from caballo.domestico.wwsimulator.replication import ReplicatedSimulation

from caballo.domestico.wwsimulator.simulation import SimulationFactory
from pdsteele.des import rngs

from caballo.domestico.wwsimulator import SIMULATION_FACTORY_CONFIG_PATH
import json


class MockInitEventHandler(EventHandler):
    def _handle(self, context):
        print("Mock init event handler called.")
        context.scheduler.schedule(Event(context.event.time + 1.0, MockEventHandler()))
class MockEventHandler(EventHandler):
    def _handle(self, context):
        print(f"Mock event handler called at {context.event.time}.")

class ArrivalCounter(EventHandler):
    def _handle(self, context):
        if not context.event.external:
            return
        if "arrivals" not in context.statistics:
            context.statistics["arrivals"] = 0
        context.statistics["arrivals"] += 1

class ReplicaInitEventHandler(EventHandler):
    def _handle(self, context):
        # mock statistic
        context.statistics["seed"] = "replica started with seed " + str(rngs.getSeed())
        # advance prng state
        rngs.random()

class TestSimulation(unittest.TestCase):
    
    def test_replication(self):
        NUM_REPLICAS = 10
        with open(SIMULATION_FACTORY_CONFIG_PATH, 'r') as file:
            data = json.load(file)
        factory = SimulationFactory()
        init_event_handler = ReplicaInitEventHandler()
        replicas = [factory.create(init_event_handler, data['exps'][0]) for _ in range(NUM_REPLICAS)]
        simulation = ReplicatedSimulation(replicas)
        simulation.run()
        print("Replicated simulation completed.")
        print("Seeds:")
        print(simulation.statistics)
    
    def test_simulation_horizon(self):
        NUM_ARRIVALS = 10
        with open(SIMULATION_FACTORY_CONFIG_PATH, 'r') as file:
            data = json.load(file)
        factory = SimulationFactory()
        simulation = factory.create(HandleFirstArrival(), data['exps'][0])
        simulation.scheduler.subscribe(ArrivalEvent, ArrivalsGeneratorSubscriber(NUM_ARRIVALS))
        simulation.scheduler.subscribe(ArrivalEvent, ArrivalCounter())
        simulation.run()

        self.assertEqual(NUM_ARRIVALS, simulation.statistics["arrivals"])
    
    def test_print_stats(self):
        NUM_ARRIVALS = 10
        NUM_REPLICAS = 10
        with open(SIMULATION_FACTORY_CONFIG_PATH, 'r') as file:
            data = json.load(file)
        factory = SimulationFactory()
        replicas = []
        for _ in range(NUM_REPLICAS):
            replica = factory.create(HandleFirstArrival(), data['exps'][0])
            replica.scheduler.subscribe(ArrivalEvent, ArrivalsGeneratorSubscriber(NUM_ARRIVALS))
            replica.scheduler.subscribe(DepartureEvent, ThroughputEstimator())
            replicas.append(replica)
        simulation = ReplicatedSimulation(replicas)
        simulation.run()
        simulation.print_statistics()


if __name__ == "__main__":
    unittest.main()