import unittest

from caballo.domestico.wwsimulator.nextevent.events import ArrivalEvent, Event, EventHandler
from caballo.domestico.wwsimulator.nextevent.handlers import ArrivalsGeneratorSubscriber, HandleFirstArrival
from caballo.domestico.wwsimulator.nextevent.replication import ReplicatedSimulationFactory

from caballo.domestico.wwsimulator.nextevent.simulation import SimulationFactory
from pdsteele.des import rngs

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
        replicas = 10
        factory = ReplicatedSimulationFactory(SimulationFactory(), replicas)
        init_event_handler = ReplicaInitEventHandler()
        simulation = factory.create(init_event_handler, seed=rngs.DEFAULT)
        simulation.run()
        print("Replicated simulation completed.")
        print("Seeds:")
        print(simulation.statistics)
    
    def test_simulation_horizon(self):
        NUM_ARRIVALS = 10
        factory = SimulationFactory()
        simulation = factory.create(HandleFirstArrival())
        simulation.scheduler.subscribe(ArrivalEvent, ArrivalsGeneratorSubscriber(NUM_ARRIVALS))
        simulation.scheduler.subscribe(ArrivalEvent, ArrivalCounter())
        simulation.run()

        self.assertEqual(NUM_ARRIVALS, simulation.statistics["arrivals"])


if __name__ == "__main__":
    unittest.main()