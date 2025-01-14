from enum import Enum

from caballo.domestico.wwsimulator.events import (ArrivalEvent, DepartureEvent,
                                                  Event, EventHandler,
                                                  JobMovementEvent)
from caballo.domestico.wwsimulator.model import Job
from caballo.domestico.wwsimulator.statistics import WelfordEstimator

_GLOBAL = "SYSTEM"

class OutputStatistic(Enum):
    RESPONSE_TIME = "response_time"
    POPULATION = "population"
    INTERARRIVAL_TIME = "interarrival"
    SERVICE_TIME = "service"
    OBSERVATION_TIME = "observation_time"
    COMPLETIONS = "completions"

    def for_node_variant(self, node: str, variant: str):
        return f"{node}-{self.value}-{variant}"
    
class Timespan():
    def __init__(self):
        self.start = None
        self.end = None

def save_statistics(output_statistic: OutputStatistic, node_id: str, estimator: WelfordEstimator, statistics: dict):
    save_statistic_value(output_statistic, node_id, estimator.avg, "avg", statistics)
    save_statistic_value(output_statistic, node_id, estimator.std, "std", statistics)
    save_statistic_value(output_statistic, node_id, estimator.max, "max", statistics)
    save_statistic_value(output_statistic, node_id, estimator.min, "min", statistics)

def save_statistic_value(output_statistic: OutputStatistic, node_id: str, value: float, variant: str, statistics: dict):
    statistics[output_statistic.for_node_variant(node_id, variant)] = value

class CompletionsEstimator(EventHandler):

    class State():
        def __init__(self):
            self._completion_count = 0
    
    def __init__(self):
        super().__init__()
        self._states = {}
        self._states[_GLOBAL] = CompletionsEstimator.State()
    
    def reset(self):
        for state in self._states.values():
            state._completion_count = 0

    
    def _estimate_throughput(self, node_id: str, event, statistics):
        if node_id not in self._states:
            self._states[node_id] = CompletionsEstimator.State()
        state = self._states[node_id]
        
        state._completion_count += 1
        save_statistic_value(OutputStatistic.COMPLETIONS, node_id, state._completion_count, "val", statistics)
            
    def _handle(self, context):
        
        event = context.event

        self.halt_if_wrong_event(event, DepartureEvent)
        
        if event.external:
            self._estimate_throughput(_GLOBAL, event, context.statistics)
        self._estimate_throughput(event.node.id, event, context.statistics)

        
class ResponseTimeEstimator(EventHandler):
    """
    Subscribes to all events.
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
        for state in self._states_by_node.values():
            state.estimator = WelfordEstimator()

    def _handle(self, context):

        event = context.event
        self.halt_if_wrong_event(event, JobMovementEvent)        

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

class ObservationTimeEstimator(EventHandler):

    class State():
        
        def __init__(self):
            self.observation_time_start = None
            self.observation_time = 0
    
    def __init__(self):
        self.reset()
    
    def _handle(self, context):

        event = context.event
        self.halt_if_wrong_event(event, Event)

        state = self.state
        if state.observation_time_start is None:
            state.observation_time_start = event.time
        else:
            observation_time_delta = event.time - state.observation_time_start
            state.observation_time += observation_time_delta
            save_statistic_value(OutputStatistic.OBSERVATION_TIME, _GLOBAL, state.observation_time, "val", context.statistics)

    def reset(self):
        self.state = ObservationTimeEstimator.State()


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
        for state in self._states_by_node.values():
            state.estimator = WelfordEstimator()

    def _update_population(self, node_id: str, event, statistics, count: int):
        if node_id not in self._states_by_node:
            self._states_by_node[node_id] = PopulationEstimator.State()
        state = self._states_by_node[node_id]

        state.population += count

        state.estimator.update(state.population)
        save_statistics(OutputStatistic.POPULATION, node_id, state.estimator, statistics)
        
    def _handle(self, context):
        job_movement = context.event
        self.halt_if_wrong_event(job_movement, JobMovementEvent)
        
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

class ServiceTimeEstimator(EventHandler):
    """
    Subscribes to job completions only
    """

    class State():
        def __init__(self):
            self.estimator = WelfordEstimator()
    
    def __init__(self):
        super().__init__()
        self._states_by_node = {}
    
    def reset(self):
        for state in self._states_by_node.values():
            state.estimator = WelfordEstimator()

    
    def _handle(self, context):
        
        event = context.event
        self.halt_if_wrong_event(event, DepartureEvent)
        
        job = event.job
        node = event.node

        if node.id not in self._states_by_node:
            self._states_by_node[node.id] = ServiceTimeEstimator.State()
        state = self._states_by_node[node.id]

        state.estimator.update(job.service_time)
        job.service_time = None

        save_statistics(OutputStatistic.SERVICE_TIME, node.id, state.estimator, context.statistics)

class InterarrivalTimeEstimator(EventHandler):
    """
    Subscribes to job arrivals only
    """

    class State():
        def __init__(self):
            self._estimator = WelfordEstimator()
            self._last_arrival_time = None
    
    def __init__(self):
        super().__init__()
        self._states = {}
        self._states[_GLOBAL] = InterarrivalTimeEstimator.State()
    
    def reset(self):
        for state in self._states.values():
            state._estimator = WelfordEstimator()
    
    def _estimate_interarrival_time(self, node_id: str, event, statistics):
        if node_id not in self._states:
            self._states[node_id] = InterarrivalTimeEstimator.State()
        state = self._states[node_id]
        
        # first completion ever observed is not used to update the estimator
        # as we need at least one sample to set a reference starting time
        if state._last_arrival_time is not None:
        
            delta = event.time - state._last_arrival_time         
            state._estimator.update(delta)

            save_statistics(OutputStatistic.INTERARRIVAL_TIME, node_id, state._estimator, statistics)
        
        state._last_arrival_time = event.time
    
    def _handle(self, context):
        
        event = context.event
        self.halt_if_wrong_event(event, ArrivalEvent)

        self._estimate_interarrival_time(event.node.id, event, context.statistics)
