import csv
import json
import os
from typing import Type

from blist import sortedlist

from caballo.domestico.wwsimulator import SIMULATION_FACTORY_CONFIG_PATH, STATISTICS_DIR
from caballo.domestico.wwsimulator.model import (FIFOQueue, Network, Node,
                                                 PSQueue, Server, State)
from caballo.domestico.wwsimulator.events import (Event,
                                                            EventContext,
                                                            EventHandler)
from caballo.domestico.wwsimulator.streams import SERVICES_BASE
from pdsteele.des import rngs


class Simulation():
    """
    A simulation represents a run of the network model with a scheduler.
    """
    def __init__(self, study:str, network: Network, initial_seed: int):
        
        self.network = network

        self.scheduler = NextEventScheduler(self)
        """
        The scheduler that manages the simulation events.
        """
        self.initial_seed = initial_seed
        """
        Initial value for the prng streams.
        """
        self.statistics = {}
        """
        A dictionary of statistics collected during the simulation run.
        type: Dict[str, Union[float, Iterable[float]]]
        key: statistic name
        value: a list of values (one value if single run, multiple values if replicated/batched run)
        """
        self.study = study
        """
        Name of the study this simulation belongs to. Used to group statistics.
        """
    
    def run(self):
        # init prng streams with initial seed
        rngs.plantSeeds(self.initial_seed)
        # consume events until the scheduler has no more events
        while self.scheduler.has_next():
            self.scheduler.next()
    
    def print_statistics(self):
        simulation_map = {'BatchMeansSimulation': 'BM_S', 'ReplicatedSimulation': 'Rep_S'}
        simulation_name = simulation_map[type(self).__name__]
        statistic_path = os.path.join(STATISTICS_DIR, self.study)
        if not os.path.exists(statistic_path):
            os.makedirs(statistic_path)

        output_file_path = os.path.join(statistic_path, "{}_{}_lambda={}_{}.csv".format(self.study, simulation_name, self.network.job_arrival_param[0], self.initial_seed))
        with open(output_file_path, "w") as output_file:
            fieldnames = ["iteration", "statistic", "value"]
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()
            for statistic, values in self.statistics.items():
                if isinstance(values, list):
                    # simulation aggregates multiple runs, we have a statistic value for each iteration 
                    for iteration in range(len(values)):
                        writer.writerow({"iteration": iteration, "statistic": statistic, "value": values[iteration]})
                else:
                    # single statistic value for single run
                    iteration = 0
                    value = values
                    writer.writerow({"iteration": iteration, "statistic": statistic, "value": value})   
    
class SimulationFactory():
    def create_network(self, experiment, lambda_val) -> Network:
        nodes = []
        prng_streams_services = {"A": SERVICES_BASE, "B": SERVICES_BASE + 1, "P": SERVICES_BASE + 2}
        node_list = experiment["nodes"]
        for node in node_list:
            server = Server(node['server_capacity'], node['server_distr']['type'], prng_streams_services[node['name']])
            if node['queue_discipline']['type'] == 'fifo':
                queue = FIFOQueue(node['queue_capacity'], node['queue_discipline']['params'])
            elif node['queue_discipline']['type'] == 'ps':
                queue = PSQueue(node['queue_capacity'], node['queue_discipline']['params'])
            else:
                raise ValueError("Queue discipline not supported")
            node = Node(node['name'], node['server_distr']['params'], server, queue)
            nodes.append(node)
        state = State(experiment['state'])
        # creazione della rete
        return Network(nodes, state, experiment['arrival_distr']['type'], [lambda_val])
    """
    factory for creating simulations.
    """
    def create(self, init_event_handler: EventHandler, data, lambda_val, network:Network=None, seed:int=rngs.DEFAULT) -> Simulation:
        simulation_study = data['simulation_study']
        if network is None:
            network = self.create_network(data, lambda_val)
        # rule out random and user input values for seed
        if seed <= 0:
            raise ValueError("Seed must be a positive integer")
        
        # builds the simulation
        simulation = Simulation(simulation_study, network, initial_seed=seed)
        simulation.scheduler.schedule(Event(0.0, init_event_handler))

        return simulation

class NextEventScheduler:
    def __init__(self, simulation: Simulation):
        self._event_list = sortedlist(key=lambda event: event.time)
        self._simulation = simulation
        self.stop=False
        self._subscribers_by_topic = {}
        self._interceptors_by_topic = {}

    def _subscribe(self, eventType: Type[Event], handler: EventHandler, subscribers: dict[Type[Event], list[EventHandler]]):
        if eventType not in subscribers:
            subscribers[eventType] = []
        subscribers[eventType].append(handler)

    def _push_notify(self, subscribers: dict[Type[Event], list[EventHandler]], context: EventContext, event: Event):
        for topic in subscribers:
            if isinstance(event, topic):
                for notify in subscribers[topic]:
                    notify(context)
    
    def has_next(self) -> bool:
        """
        Return true if there are more events to process.
        """
        return not self.stop and len(self._event_list) > 0
        
    def next(self):
        """
        Consumes the event with the earliest scheduled time in the event list
        and calls the event handler.
        """
        if len(self._event_list) == 0:
            raise ValueError("No more events to process.")
        
        # gets event from event list and creates context
        event = self._event_list.pop(0)
        if not event.is_cancelled:

            context = EventContext(event, self._simulation.network, self, self._simulation.statistics)

            # intercepts event
            self._push_notify(self._interceptors_by_topic, context, event)

            # consumes event
            event.handle(context)

            # push notify subscribers
            self._push_notify(self._subscribers_by_topic, context, event)

    def schedule(self, event: Event, delay: float=0.0):
        """
        Adds the event to the event list with an optional delay
        added to its scheduling time.
        """
        event.time += delay
        self._event_list.add(event)
    
    def cancel(self, event: Event):
        """
        Cancels the event from the scheduling. A cancelled event is not processed, so its handler
        is not called nor are its subscribers/interceptors notified.
        """
        event.is_cancelled = True
    
    def subscribe(self, eventType: Type[Event], handler: EventHandler):
        """
        Subscribes an event handler to call after an event of the specified type is consumed.
        """
        self._subscribe(eventType, handler, self._subscribers_by_topic)
    
    def intercept(self, eventType: Type[Event], handler: EventHandler):
        """
        Subscribes an event handler to call before an event of the specified type is consumed.
        Such handler can change the context of the event before it is actually processed.
        """
        self._subscribe(eventType, handler, self._interceptors_by_topic)
    
    def reset_subscribers(self, context: EventContext):
        """
        For each subscriber, tries to reset it.
        A subscriber must implement a reset method if it has a state that must be reset
        during a simulation run (i.e. among batches).
        @param context: context of the event triggering the reset
        """
        for topic in self._subscribers_by_topic:
            seen = []
            for subscriber in self._subscribers_by_topic[topic]:
                if subscriber not in seen:
                    try:
                        subscriber.reset(context)
                    except AttributeError:
                        pass
                    seen.append(subscriber)