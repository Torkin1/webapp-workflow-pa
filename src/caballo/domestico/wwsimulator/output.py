from enum import Enum
from typing import Iterable
from caballo.domestico.wwsimulator.model import Node
from caballo.domestico.wwsimulator.nextevent.events import DepartureEvent, EventHandler
from caballo.domestico.wwsimulator.statistics import WelfordEstimator, WelfordTimeAveragedEstimator


class OutputStatistic(Enum):
    THROUGHPUT = "throughput"

    def for_node_variant(self, node: Node, variant: str):
        return f"{node.id}-{self.value}-{variant}"

class ThroughputState():
    def __init__(self):
        self._estimator = WelfordEstimator()
        self._last_completion_time = 0
        self._concurrent_completions = 0

class ThroughputEstimator(EventHandler):
    """
    Subscribes to job completions only
    """
    def __init__(self):
        super().__init__()
        self._states = {}
    
    def _handle(self, context):
        
        event = context.event

        if not isinstance(event, DepartureEvent):
            raise ValueError(f"ThroughputEstimator can only handle DepartureEvent, got {type(event)}")

        # ignore departure if at time 0 to avoid division by zero
        if event.time == 0:
            return
        
        # estimates time averaged throughput by computing the reciprocal of the time
        # between two consecutive job completions
        node = event.node
        if node.id not in self._states:
            self._states[node.id] = ThroughputState()
        state = self._states[node.id]
        
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
            context.statistics[OutputStatistic.THROUGHPUT.for_node_variant(node, "avg")] = state._estimator.avg
            context.statistics[OutputStatistic.THROUGHPUT.for_node_variant(node, "std")] = state._estimator.std
            context.statistics[OutputStatistic.THROUGHPUT.for_node_variant(node, "max")] = state._estimator.max
            context.statistics[OutputStatistic.THROUGHPUT.for_node_variant(node, "min")] = state._estimator.min


        