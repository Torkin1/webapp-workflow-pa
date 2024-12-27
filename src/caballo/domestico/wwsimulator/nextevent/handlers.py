from caballo.domestico.wwsimulator.nextevent.events import EventContext, EventHandler, Event, ArrivalEvent, DepartureEvent, MisurationEvent
from caballo.domestico.wwsimulator.model import Job

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
                new_job = Job(0, context.event.job.job_id+1)
                arrival = ArrivalEvent(context.event.time + arrival_time, HandleArrival(), new_job, context.network.get_node('A'))
                arrival.external = True
                context.scheduler.schedule(arrival)


class HandleArrival(EventHandler):
    def __init__(self):
        super().__init__()

    def _handle(self, context: EventContext):
        job_class = context.event.job.class_id
        job_id = context.event.job.job_id

        job_server = context.event.node.id
        job_server_int = context.event.node.node_map(job_server)
        print(f"Arrival of job {job_id} of class {job_class} at server {job_server}:{job_server_int}, external? {context.event.external}")
        # aggiornamento dello stato del sistema
        context.network.state.update((job_server_int, job_class), True)

        # generazione evento di departure per il job corrente
        service_rate = context.network.nodes[job_server_int].service_rate[job_class]
        service_time = context.event.node.server.get_service([service_rate])
        arrival_time = context.event.time
        queue_time = context.event.node.queue.get_queue_time(context.event.job, arrival_time)
        print(f"Queue time: {queue_time}")
        departure_time = arrival_time + service_time + queue_time
        context.network.nodes[job_server_int].queue.register_last_departure(context.event.job, departure_time)

        context.event.job.class_id = job_class+1 if job_server != 'A' else job_class
        departure = DepartureEvent(departure_time, HandleDeparture(), context.event.job, context.event.node)
        departure.external = True if (job_server == 'A' and job_class == 2) else False

        # scheduling dell'evento di departure
        context.scheduler.schedule(departure)        

class HandleDeparture(EventHandler):
    def __init__(self):
        super().__init__()

    def _handle(self, context: EventContext):
        job_server_str = context.event.node.id
        job_server = context.event.node.node_map(job_server_str)
        job_class = context.event.job.class_id
    
        print(f"Departure of job {context.event.job.job_id} of class {job_class} from server {job_server_str}:{job_server}, external? {context.event.external}")

        # aggiornamento dello stato del sistema
        decrease = job_class-1 if job_class > 0 else job_class
        context.network.state.update((job_server, decrease), False)
        
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
        job = Job(0, 0)
        node = context.network.nodes[0]
        arrival = ArrivalEvent(0.0, HandleArrival(), job, node)
        arrival.external = True
        context.scheduler.schedule(arrival)
        