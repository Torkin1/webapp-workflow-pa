from abc import ABC
from caballo.domestico.wwsimulator.model import Job, Network, Server, Queue, Node, State
from caballo.domestico.wwsimulator.nextevent.events import NextEventScheduler, ArrivalEvent, EventContext, JobMovementEvent
from caballo.domestico.wwsimulator.nextevent.handlers import HandleArrival

class Simulation():
    """
    A simulation represents a run of the network model with a scheduler.
    """
    def __init__(self, scheduler: NextEventScheduler):
        self.scheduler = scheduler
    
    def run(self):
        while self.scheduler.has_next():
            self.scheduler.next()

class SimulationFactory(ABC):
    def create(self) -> Simulation:
        pass

if __name__ == "__main__":
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

    # creazione dello scheduler
    scheduler = NextEventScheduler(network)

    # creazione di un evento di arrivo
    job = Job(0, 0)
    first_arrival = JobMovementEvent(0.0, HandleArrival(), job, server_A)
    context = EventContext(first_arrival, network, scheduler)
    first_arrival.handle(context)
    i = 0
    while scheduler.has_next():
            scheduler.next()

 