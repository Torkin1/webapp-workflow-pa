from abc import ABC, abstractmethod

from blist import sortedlist

from caballo.domestico.wwsimulator.model import Network
from caballo.domestico.wwsimulator.nextevent.events import (Event, EventContext,
                                                            EventHandler, DepartureEvent, 
                                                            ArrivalEvent, JobMovementEvent
                                                            )
from caballo.domestico.wwsimulator.model import State, Node, Server, Queue, Job
from caballo.domestico.wwsimulator.nextevent.handlers import HandleArrival

from pdsteele.des import rngs

import json

class Simulation():
    """
    A simulation represents a run of the network model with a scheduler.
    """
    def __init__(self, network: Network, initial_seed: int, statistics: dict, type: bool=False):
        
        self.network = network

        self.type = type
        """
        Is the simulation a batch means simulation?
        """

        self.scheduler = NextEventScheduler(self)
        """
        The scheduler that manages the simulation events.
        """
        self.initial_seed = initial_seed
        """
        Initial value for the prng streams.
        """
        self.statistics = statistics
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
        with open('config.json', 'r') as file:
            data = json.load(file)
        nodes = []
        for experiment in data['exps']:
            is_batch = True if experiment['type'] == "batchmeans" else False
            node_list = experiment["nodes"]
            for node in node_list:
                server = Server(node['name'], node['server_capacity'], node['server_distr']['type'])
                queue = Queue(node['name'], node['queue_capacity'], node['queue_discipline']['type'])
                node = Node(node['name'], node['server_distr']['params'], server, queue)
                nodes.append(node)

            state = State(experiment['state'])

            # creazione della rete
            return Network(nodes, state, experiment['arrival_distr']['type'], experiment['arrival_distr']['params']), is_batch
    """
    factory for creating simulations.
    """
    def create(self, seed=rngs.DEFAULT) -> Simulation:
        network, is_batch = self.create_network()
        # rule out random and user input values for seed
        if seed < 0:
            raise ValueError("Seed must be a positive integer")
        
        # builds the simulation
        statistics = {'jobs':0} if is_batch else {}
        simulation = Simulation(network, initial_seed=seed, statistics=statistics)
        simulation.scheduler.schedule(JobMovementEvent(0.0, HandleArrival(), Job(0, 0), network.nodes[0].server))
        simulation.initial_seed = seed
        simulation.type = is_batch


        return simulation
        
class NextEventScheduler:
    def __init__(self, simulation: Simulation):
        self._event_list = sortedlist(key=lambda event: event.time)
        self._simulation = simulation
        self.stop=False
    
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
        event = self._event_list.pop(0)
        # se l'evento è un arrivo devo cercare nell'event_list, la prossima departure dallo stesso 
        # server ed aggiornare il time dell'arrival corrente sommandogli quel valore solo se è FIFO
        queue = self._simulation.network.nodes[event.server.node_map(event.server.id)].queue
 
        if queue.queue_policy == 'fifo' and isinstance(event.handle, ArrivalEvent):
            print('fifo')
            for e in self._event_list:
                if e.server.id == event.server.id and isinstance(e.handler, DepartureEvent):
                    event.time += e.time
                    break
        context = EventContext(event, self._simulation.network, self, self._simulation.statistics, self._simulation.type)
        event.handle(context)

    def schedule(self, event: Event, delay: float=0.0):
        """
        Adds the event to the event list with an optional delay
        added to its scheduling time.
        """
        event.time += delay
        self._event_list.add(event)