import unittest

from caballo.domestico.wwsimulator.model import Network
from caballo.domestico.wwsimulator.nextevent.events import Event, EventHandler
from caballo.domestico.wwsimulator.nextevent.events import NextEventScheduler
from caballo.domestico.wwsimulator.nextevent.simulation import Simulation, SimulationFactory

class MockInitEventHandler(EventHandler):
    def _handle(self, context):
        print("Mock init event handler called.")
        context.scheduler.schedule(Event(1.0, MockEventHandler()))
class MockEventHandler(EventHandler):
    def _handle(self, context):
        print(f"Mock event handler called at {context.event.time}.")

class MockSimulationFactory(SimulationFactory):
    def create(self):
        network = Network()
        scheduler = NextEventScheduler(network)
        init = Event(0.0, MockInitEventHandler())
        scheduler.schedule(init)
        simulation = Simulation(scheduler)
        return simulation

class TestSimulation(unittest.TestCase):
    def test_simulation(self):
        sim_factory = MockSimulationFactory()
        simulation = sim_factory.create()
        simulation.run()
        print("Simulation completed.")

if __name__ == "__main__":
    unittest.main()