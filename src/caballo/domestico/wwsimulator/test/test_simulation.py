import unittest

from caballo.domestico.wwsimulator.model import Job, Network, Node, Queue, Server, State
from caballo.domestico.wwsimulator.nextevent.events import Event, EventHandler, JobMovementEvent
from caballo.domestico.wwsimulator.nextevent.events import NextEventScheduler
from caballo.domestico.wwsimulator.nextevent.handlers import HandleArrival
from caballo.domestico.wwsimulator.nextevent.simulation import Simulation, SimulationFactory

from pdsteele.des import rngs

class MockInitEventHandler(EventHandler):
    def _handle(self, context):
        print("Mock init event handler called.")
        context.scheduler.schedule(Event(1.0, MockEventHandler()))
class MockEventHandler(EventHandler):
    def _handle(self, context):
        print(f"Mock event handler called at {context.event.time}.")

class MockSimulationFactory(SimulationFactory):
    def _create_network(self) -> Network:
        return Network(None, None)
    def _create_init_event(self, network: Network) -> Event:
        return Event(0.0, MockInitEventHandler())
class MockSimulationFactory2(SimulationFactory):
    def _create_network(self) -> Network:
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
        matrix = [[0 for _ in range(3)] for _ in range(3)]
        state = State(matrix)

        # creazione della rete
        network = Network(nodes, state)
        return network

    def _create_init_event(self, network: Network) -> Event:
        # creazione del primo evento di arrivo
        job = Job(0, 0)
        for n in network.nodes:
            if n.id == "A":
                server_A = n.server
                break
        first_arrival = JobMovementEvent(0.0, HandleArrival(), job, server_A)
        return first_arrival

class TestSimulation(unittest.TestCase):
    def test_simulation(self):
        sim_factory = MockSimulationFactory()
        simulation = sim_factory.create(seed=rngs.DEFAULT)
        simulation.run()
        print("Simulation completed.")
    
    def test_simulation2(self):
        factory = MockSimulationFactory2()
        simulation = factory.create(seed=rngs.DEFAULT)
        simulation.run()


if __name__ == "__main__":
    unittest.main()