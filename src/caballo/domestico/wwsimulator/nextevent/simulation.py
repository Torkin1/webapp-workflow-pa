import json
from typing import Type

from blist import sortedlist

from caballo.domestico.wwsimulator import SIMULATION_FACTORY_CONFIG_PATH
from caballo.domestico.wwsimulator.model import (FIFOQueue, Network, Node,
                                                 PSQueue, Server, State)
from caballo.domestico.wwsimulator.nextevent.events import (Event,
                                                            EventContext,
                                                            EventHandler)
from caballo.domestico.wwsimulator.toolbox import Clonable
from pdsteele.des import rngs


class Simulation():
    """
    A simulation represents a run of the network model with a scheduler.
    """
    def __init__(self, network: Network, initial_seed: int):
        
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
        type: Dict[str, Iterable[float]]
        key: statistic name
        value: a list of values (one value if single run, multiple values if replicated/batched run)
        """
    
    def run(self):
        # init prng streams with initial seed
        rngs.plantSeeds(self.initial_seed)
        # consume events until the scheduler has no more events
        while self.scheduler.has_next():
            self.scheduler.next()
    
class SimulationFactory():
    def create_network(self):
        with open(SIMULATION_FACTORY_CONFIG_PATH, 'r') as file:
            data = json.load(file)
        nodes = []
        for experiment in data['exps']:
            node_list = experiment["nodes"]
            for node in node_list:
                server = Server(node['server_capacity'], node['server_distr']['type'])
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
            return Network(nodes, state, experiment['arrival_distr']['type'], experiment['arrival_distr']['params'])
    """
    factory for creating simulations.
    """
    def create(self, init_event_handler: EventHandler, network:Network=None, seed:int=rngs.DEFAULT) -> Simulation:
        if network is None:
            network = self.create_network()
        # rule out random and user input values for seed
        if seed <= 0:
            raise ValueError("Seed must be a positive integer")
        
        # builds the simulation
        simulation = Simulation(network, initial_seed=seed)
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