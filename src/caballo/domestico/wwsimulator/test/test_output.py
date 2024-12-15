import unittest

from caballo.domestico.wwsimulator.model import Job, Node, Queue, Server
from caballo.domestico.wwsimulator.nextevent.events import DepartureEvent, Event, EventHandler, JobMovementEvent, StopEvent
from caballo.domestico.wwsimulator.nextevent.simulation import SimulationFactory
from caballo.domestico.wwsimulator.output import ThroughputEstimator

class MockHandler(EventHandler):
    
    def _handle(self, context):
        pass

class MockCompletion(DepartureEvent):
    def __init__(self, time: float):
        super().__init__(time,
                          MockHandler(),
                          Job(0, 0),
                          Node("myNode", [], Server("myServer",
                                                    0,
                                                    "exponential"),
                                             Queue("myQueue",
                                                    0,
                                                    "fifo",
                                                    [])))
    

class InitHandler(EventHandler):
    def _handle(self, context):
        scheduler = context.scheduler
        for i in range(1000):
            if i % 2 == 0:
                scheduler.schedule(MockCompletion(i))


class TestOutput(unittest.TestCase):
    def test_throughput(self):

        factory = SimulationFactory()
        simulation = factory.create(InitHandler())
        throughput_estimator = ThroughputEstimator()
        simulation.scheduler.subscribe(MockCompletion, throughput_estimator)

        simulation.run()
        print(simulation.statistics)
        

if __name__ == "__main__":
    unittest.main()