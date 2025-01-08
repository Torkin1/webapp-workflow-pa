from caballo.domestico.wwsimulator.events import EventContext, EventHandler, Event, ArrivalEvent, DepartureEvent, MisurationEvent
from caballo.domestico.wwsimulator.model import Job, Node, PSQueue, State
from blist import sortedlist

class ArrivalsGeneratorSubscriber(EventHandler):
    """
    Subscribes for ArrivalEvents and counts the number of observed external arrivals.
    It generates new external arrivals until the maximum number is reached.
    """
    
    def __init__(self, max_arrivals: int):
        super().__init__()
        self.max_arrivals = max_arrivals
        self.observed_arrivals = 0
    
    def _handle(self, context):
        event = context.event
        if not isinstance(event, ArrivalEvent):
            raise ValueError(f"{__class__.__qualname__} can only handle {ArrivalEvent.__qualname__}.")
        
        if event.external:
            self.observed_arrivals += 1

            # rigenerazione evento di arrival dall'esterno del sistema
            if self.observed_arrivals < self.max_arrivals:
                arrival_time = context.network.get_arrivals()
                new_job = Job(0, context.event.job.job_id+1, 0)
                arrival = ArrivalEvent(context.event.time + arrival_time, HandleArrival(), new_job, context.network.get_node('A'))
                arrival.external = True
                context.scheduler.schedule(arrival)

def _update_departures(now, node: Node, num_jobs_in_service, old_num_jobs_in_service, scheduler,):
        
    # La pesca random è sul tempo di servizio, che chiamiamo S. 
    # Sia Srem il tempo di servizio rimanente.
    # Sia Drem la domanda rimanente e mu/N il rate di servizio, allora Srem = Drem/(mu/N).
    # Prendiamo nuovo rate mu2 = mu/N*, dove N* è il nuovo numero dei job in servizio.
    # Sia Srem2 = Drem/mu2 il tempo di servizio che ci metterebbe con mu2.
    # Ti ricavi Drem = Srem•mu/N => Srem2 = (Srem•mu/N)/(mu/N*) = Srem • N*/N
    # Ora i job vanno schedulati a current time + Srem2
    scheduled_departures = node.scheduled_departures
    for departure in scheduled_departures.values():

        # cancel old departures and schedules a new one after recalculating the remaining service time
        scheduler.cancel(departure)
        remaining_service_time = (departure.time - now) * (num_jobs_in_service / old_num_jobs_in_service)
        departure_time = now + remaining_service_time
        new_departure = DepartureEvent(departure_time, HandleDeparture(), departure.job, departure.node)
        new_departure.external = departure.external
        scheduler.schedule(new_departure)
        node.scheduled_departures[departure.job.job_id] = new_departure

def _get_num_jobs_in_node(node: Node, state: State):
    node_index = node.node_map(node.id)
    num_jobs_in_node = sum(state.get_node_state(node_index))
    return num_jobs_in_node

class HandleArrival(EventHandler):
        
    def __init__(self):
        super().__init__()
    
    def _handle(self, context: EventContext):
        
        job = context.event.job
        job_class = job.class_id

        job_server = context.event.node.id
        job_server_int = context.event.node.node_map(job_server)
        
        # aggiornamento dello stato del sistema
        context.network.state.update((job_server_int, job_class), True)

        # generazione evento di departure per il job corrente
        service_rate = context.network.nodes[job_server_int].service_rate[job_class]
        
        # rescale service rate if we are using a PS node
        node = context.event.node
        if type(node.queue) is PSQueue:
                        
            # calc num jobs in service using state.
            num_jobs_in_node = len(node.scheduled_departures) + 1
            old_num_jobs_in_node = num_jobs_in_node - 1
            service_rate = service_rate / num_jobs_in_node

            # update departure times for already scheduled jobs
            now = context.event.time
            _update_departures(now, node, num_jobs_in_node, old_num_jobs_in_node, context.scheduler)


        service_time = context.event.node.server.get_service([service_rate])
        context.event.job.service_time = service_time
        arrival_time = context.event.time
        queue_time = context.event.node.queue.get_queue_time(context.event.job, arrival_time)
        departure_time = arrival_time + service_time + queue_time
        context.network.nodes[job_server_int].queue.register_last_departure(context.event.job, departure_time)

        context.event.job.class_id = job_class+1 if job_server != 'A' else job_class
        departure = DepartureEvent(departure_time, HandleDeparture(), context.event.job, context.event.node)
        departure.external = True if (job_server == 'A' and job_class == 2) else False

        # scheduling dell'evento di departure
        context.scheduler.schedule(departure)

        # register departure to possibly update by PS rule in case another arrival
        if type(node.queue) is PSQueue:
            node.scheduled_departures[job.job_id] = departure      

class HandleDeparture(EventHandler):
    def __init__(self):
        super().__init__()

    def _handle(self, context: EventContext):
        job = context.event.job
        job_server_str = context.event.node.id
        job_server = context.event.node.node_map(job_server_str)
        job_class = context.event.job.class_id
    
        # aggiornamento dello stato del sistema
        decrease = job_class-1 if job_class > 0 else job_class
        context.network.state.update((job_server, decrease), False)

        # we need to update the departure times of the other jobs in service
        # since now they are receiving a bigger service rate
        node = context.event.node
        if type(node.queue) is PSQueue:
            # remove departure from scheduled departures of this node
            node.scheduled_departures.pop(job.job_id)
            now = context.event.time
            num_jobs_in_node = len(node.scheduled_departures)
            old_jobs_in_node = num_jobs_in_node + 1
            _update_departures(now, node, num_jobs_in_node, old_jobs_in_node, context.scheduler)

        
        if not (job_class == 2 and job_server_str == 'A'):
            if job_server_str in ['B', 'P']:
                new_server_id = 'A'
            elif job_server_str == 'A' and job_class == 0:
                new_server_id = 'B'
            else:
                new_server_id = 'P'
            next_node = context.network.nodes[context.event.node.node_map(new_server_id)]
            arrival = ArrivalEvent(context.event.time, HandleArrival(), context.event.job, next_node)
            context.scheduler.schedule(arrival)

class HandleInit(EventHandler):
    def __init__(self):
        super().__init__()

class HandleFirstArrival(HandleInit):
    def __init__(self):
        super().__init__()

    def _handle(self, context: EventContext):
        job = Job(0, 0, 0)
        node = context.network.nodes[0]
        arrival = ArrivalEvent(0.0, HandleArrival(), job, node)
        arrival.external = True
        context.scheduler.schedule(arrival)
        