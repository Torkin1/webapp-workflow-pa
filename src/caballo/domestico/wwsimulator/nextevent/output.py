"""
NOTE: the estimators (reasonably) assume that a departure 
shall always be preceded by an arrival
"""

from enum import Enum
from typing import Iterable
from caballo.domestico.wwsimulator.model import Job
from caballo.domestico.wwsimulator.nextevent.events import ArrivalEvent, DepartureEvent, EventHandler, JobMovementEvent
from caballo.domestico.wwsimulator.statistics import WelfordEstimator

_GLOBAL = "SYSTEM" 

class OutputStatistic(Enum):
    THROUGHPUT = "throughput"
    RESPONSE_TIME = "response_time"
    POPULATION = "population"

    def for_node_variant(self, node: str, variant: str):
        return f"{node}-{self.value}-{variant}"
    
class Timespan():
    def __init__(self):
        self.start = None
        self.end = None

def save_statistics(output_statistic: OutputStatistic, node_id: str, estimator: WelfordEstimator, statistics: dict):
    statistics[output_statistic.for_node_variant(node_id, "avg")] = estimator.avg
    statistics[output_statistic.for_node_variant(node_id, "std")] = estimator.std
    statistics[output_statistic.for_node_variant(node_id, "max")] = estimator.max
    statistics[output_statistic.for_node_variant(node_id, "min")] = estimator.min

class ThroughputEstimator(EventHandler):
    """
    Subscribes to job completions only
    """

    class State():
        def __init__(self):
            self._estimator = WelfordEstimator()
            self._last_completion_time = 0
            self._concurrent_completions = 0
    
    def __init__(self):
        super().__init__()
        self._states = {}
        self._states[_GLOBAL] = ThroughputEstimator.State()
    
    def reset(self):
        self.__init__()
    
    def _estimate_throughput(self, node_id: str, event, statistics):
        if node_id not in self._states:
            self._states[node_id] = ThroughputEstimator.State()
        state = self._states[node_id]
        
        delta = event.time - state._last_completion_time
        state._concurrent_completions += 1

        # concurrent completions are counted in the next non-concurrent sample.
        #
        # |---------------------------------------| delta
        # ^                                       ^
        # n concurrent completions,               first non-concurrent completion,
        # no sample update occurs                 sample update will count the 
        #                                         concurrent completions too 
        #                                         
        if delta > 0:
            sample = state._concurrent_completions / delta
            state._estimator.update(sample)
            state._last_completion_time = event.time
            state._concurrent_completions = 0

            # update throughput in statistics object
            save_statistics(OutputStatistic.THROUGHPUT, node_id, state._estimator, statistics)
    
    def _handle(self, context):
        
        event = context.event

        if not isinstance(event, DepartureEvent):
            raise ValueError(f"ThroughputEstimator can only handle DepartureEvent, got {type(event)}")

        # ignore departure if at time 0 to avoid division by zero
        if event.time == 0:
            return
        
        # estimates time averaged throughput by computing the reciprocal of the time
        # between two consecutive job completions
        if event.external:
            self._estimate_throughput(_GLOBAL, event, context.statistics)
        self._estimate_throughput(event.node.id, event, context.statistics)

        if context.new_batch:
            self.reset()

class ResponseTimeEstimator(EventHandler):
    """
    Subscribes to job movements (arrivals and departures).
    """
    
    class State():
        def __init__(self):
            self.estimator = WelfordEstimator()
            self.timespans_jobs_in_residence = {}
            """
            Jobs currently in service by id.
            """
    
    def __init__(self):
        super().__init__()
        self._states_by_node = {}
        self._states_by_node[_GLOBAL] = ResponseTimeEstimator.State()
    
    def reset(self):
        self.estimator = WelfordEstimator()
        self.timespans_jobs_in_residence = {}
        

    def _handle(self, context):

        event = context.event
        if not isinstance(event, JobMovementEvent):
            raise ValueError(f"ResponseTimeEstimator can only subscribe to JobMovementEvent, got {type(event)}")        

        if isinstance(event, DepartureEvent):
            self._handle_departure(context)
        elif isinstance(event, ArrivalEvent):
            self._handle_arrival(context)
        else:
            raise ValueError(f"ResponseTimeEstimator can only handle ArrivalEvent and DepartureEvent, got {type(event)}")

    def _register_arrival(self, node_id: str, job: Job, arrival: ArrivalEvent):
        if node_id not in self._states_by_node:
            self._states_by_node[node_id] = ResponseTimeEstimator.State()
        state = self._states_by_node[node_id]

        residence_timespan = Timespan()
        residence_timespan.start = arrival.time

        state.timespans_jobs_in_residence[job.job_id] = residence_timespan
        
    
    def _estimate_response_time(self, node: str, job: Job, departure: DepartureEvent, statistics):
        state = self._states_by_node[node]
        
        residence_timespan = state.timespans_jobs_in_residence[job.job_id]
        residence_timespan.end = departure.time
        response_time = residence_timespan.end - residence_timespan.start

        state.estimator.update(response_time)
        save_statistics(OutputStatistic.RESPONSE_TIME, node, state.estimator, statistics)
    
    def _handle_arrival(self, context):
        job_movement = context.event
        job = context.event.job
        node = context.event.node

        # global statistic
        if job_movement.external:
            self._register_arrival(_GLOBAL, job, job_movement)

        # local statistic                    
        self._register_arrival(node.id, job, job_movement)

    def _handle_departure(self, context):
        node = context.event.node
        job = context.event.job
        job_movement = context.event

        # compute response time of job
        if job_movement.external:
            self._estimate_response_time(_GLOBAL, job, job_movement, context.statistics)
        self._estimate_response_time(node.id, job, job_movement, context.statistics)

        if context.new_batch:
            self.reset()

class PopulationEstimator(EventHandler):
    """
    Subscribes to job movements
    """

    class State():
        def __init__(self):
            self.estimator = WelfordEstimator()
            self.population = 0
    
    def __init__(self):
        super().__init__()
        self._states_by_node = {}
        self._states_by_node[_GLOBAL] = PopulationEstimator.State()
    
    def reset(self):
        self.__init__()

    def _update_population(self, node_id: str, event, statistics, count: int):
        if node_id not in self._states_by_node:
            self._states_by_node[node_id] = PopulationEstimator.State()
        state = self._states_by_node[node_id]

        state.population += count

        state.estimator.update(state.population)
        save_statistics(OutputStatistic.POPULATION, node_id, state.estimator, statistics)
        
    def _handle(self, context):
        job_movement = context.event
        if not isinstance(job_movement, JobMovementEvent):
            raise ValueError(f"PopulationEstimator can only subscribe to JobMovementEvent, got {type(job_movement)}")
        
        # we increase o decrease the population count based on the job movement direction
        if isinstance(job_movement, ArrivalEvent):
            count = 1
        elif isinstance(job_movement, DepartureEvent):
            count = -1
        else:
            raise ValueError(f"PopulationEstimator can only handle ArrivalEvent and DepartureEvent, got {type(job_movement)}")        
        
        statistics = context.statistics
        if job_movement.external:
            self._update_population(_GLOBAL, job_movement, statistics, count)
        self._update_population(job_movement.node.id, job_movement, statistics, count)
        if context.statistics == {}:
            print("statistics is empty")
        if context.new_batch:
            self.reset()
