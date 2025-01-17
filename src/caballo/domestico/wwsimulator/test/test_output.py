import unittest

from caballo.domestico.wwsimulator.model import Job, Node, Queue, Server
from caballo.domestico.wwsimulator import simulation
from caballo.domestico.wwsimulator.events import ArrivalEvent, DepartureEvent, Event, EventHandler, JobMovementEvent
from caballo.domestico.wwsimulator.simulation import SimulationFactory
from caballo.domestico.wwsimulator.output import PopulationEstimator, ResponseTimeEstimator, ThroughputEstimator

class MockHandler(EventHandler):
    
    def _handle(self, context):
        pass

class MockCompletion(DepartureEvent):
    def __init__(self, time: float, job_id=0):
        super().__init__(time,
                          MockHandler(),
                          Job(job_id=job_id, class_id=0),
                          Node("myNode", [], Server("myServer",
                                                    0,
                                                    "exponential"),
                                             Queue("myQueue",
                                                    0,
                                                    "fifo",
                                                    [])))
        self.external = True
    

class InitHandler(EventHandler):
    def _handle(self, context):
        scheduler = context.scheduler
        for i in range(1000):
            if i % 2 == 0:
                scheduler.schedule(MockCompletion(i))


class MockArrival(ArrivalEvent):
    def __init__(self, time):
        super().__init__(time,
                            lambda context: context.scheduler.schedule(MockCompletion(time, context.event.job.job_id)),
                            Job(job_id=time, class_id=0),
                            Node("myNode", [], Server("myServer",
                                                        0,
                                                        "exponential"),
                                            Queue("myQueue",
                                                    0,
                                                    "fifo",
                                                    [])))
        self.external = True
def init_handler(context):
    for i in range(1000): 
        context.scheduler.schedule(MockArrival(i))

class TestOutput(unittest.TestCase):
    def test_throughput(self):

        factory = SimulationFactory()
        simulation = factory.create(InitHandler())
        throughput_estimator = ThroughputEstimator()
        simulation.scheduler.subscribe(MockCompletion, throughput_estimator)

        simulation.run()
        print(simulation.statistics)
    
    def test_response_time(self):
        factory = SimulationFactory()
        simulation = factory.create(init_handler)
        response_time_estimator = ResponseTimeEstimator()
        simulation.scheduler.subscribe(JobMovementEvent, response_time_estimator)

        simulation.run()
        print(simulation.statistics)
    
    def test_population(self):
        factory = SimulationFactory()
        simulation = factory.create(init_handler)
        simulation.scheduler.subscribe(JobMovementEvent, PopulationEstimator())

        simulation.run()
        print(simulation.statistics)
        
        

if __name__ == "__main__":
    unittest.main()