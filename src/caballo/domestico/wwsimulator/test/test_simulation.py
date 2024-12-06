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
        context.scheduler.schedule(Event(1.0, MockEventHandler()))
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

def create_network() -> Network:
    # creazione dei tre nodi
    server_A = Server("A", 100, 'exp')
    queue_A = Queue("A", 100)
    node_A = Node("A", [0.2, 0.4, 0.2], server_A, queue_A)

    server_B = Server("B", 100, 'exp')
    queue_B = Queue("B", 100)
    node_B = Node("B", [0.8, 0, 0], server_B, queue_B)

    server_P = Server("P", 100, 'exp')
    queue_P = Queue("P", 100)
    node_P = Node("P", [0, 0.4, 0], server_P, queue_P)

    nodes = [node_A, node_B, node_P]

    # inizializzazione stato vuoto del sistema
    state = State(3, 3)

    # creazione della rete
    network = Network(nodes, state)
    return network

class ReplicaInitEventHandler(EventHandler):
    def _handle(self, context):
        if "run" not in context.statistics:
            context.statistics["seeds"] = []
        # mock statistic
        context.statistics["seeds"].append("replica started with seed " + str(rngs.getSeed()))
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
        simulation = factory.create(network=create_network(), seed=rngs.DEFAULT)
        simulation.run()
    
    def test_replication(self):
        replicas = 10
        factory = ReplicatedSimulationFactory(SimulationFactory(), replicas)
        init_event_handler = ReplicaInitEventHandler()
        simulation = factory.create(create_network(), init_event_handler, seed=rngs.DEFAULT)
        simulation.run()
        print("Replicated simulation completed.")
        print("Seeds:")
        print(simulation.statistics)


if __name__ == "__main__":
    unittest.main()