import unittest

from caballo.domestico.wwsimulator.model import Job, Network, Node, Queue, Server, State
from caballo.domestico.wwsimulator.nextevent.events import Event, EventHandler, JobMovementEvent
from caballo.domestico.wwsimulator.nextevent.handlers import HandleArrival
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

class MockSimulationFactory(SimulationFactory):
    def _create_init_event_handler(self, network: Network) -> Event:
        return Event(0.0, MockInitEventHandler())
class MockSimulationFactoryNetwork(SimulationFactory):
    def _create_init_event_handler(self, network: Network) -> Event:
        # creazione del primo evento di arrivo
        job = Job(0, 0)
        for n in network.nodes:
            if n.id == "A":
                server_A = n.server
                break
        first_arrival = JobMovementEvent(0.0, HandleArrival(), job, server_A)
        return first_arrival

class ReplicaInitEventHandler(EventHandler):
    def _handle(self, context):
        # mock statistic
        context.statistics["seed"] = "replica started with seed " + str(rngs.getSeed())
        # advance prng state
        rngs.random()
class TestSimulation(unittest.TestCase):
    def test_simulation(self):
        sim_factory = MockSimulationFactory()
        simulation = sim_factory.create(Network(None, None), seed=rngs.DEFAULT)
        simulation.run()
        print("Simulation completed.")
    
    def test_simulation_network(self):
        factory = MockSimulationFactoryNetwork()
        simulation = factory.create(MockInitEventHandler(), seed=rngs.DEFAULT)
        simulation.run()
    
    def test_replication(self):
        replicas = 10
        factory = ReplicatedSimulationFactory(SimulationFactory(), replicas)
        init_event_handler = ReplicaInitEventHandler()
        simulation = factory.create(init_event_handler, seed=rngs.DEFAULT)
        simulation.run()
        print("Replicated simulation completed.")
        print("Seeds:")
        print(simulation.statistics)


if __name__ == "__main__":
    unittest.main()