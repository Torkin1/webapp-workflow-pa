from caballo.domestico.wwsimulator.nextevent.events import EventContext, EventHandler, Event, ArrivalEvent, DepartureEvent, MisurationEvent
from caballo.domestico.wwsimulator.model import Job, Server
import pdsteele.des.rvgs as des

class HandleArrival(EventHandler):
    def __init__(self):
        super().__init__()

    def _handle(self, context: EventContext):
        job_class = context.event.job.class_id
        job_id = context.event.job.job_id

        job_server = context.event.node.id
        job_server_int = context.event.node.node_map(job_server)
        # TODO: rimuovere limite job
        if job_id < 10:
            print(f"Arrival of job {job_id} of class {job_class} at server {job_server}:{job_server_int}, external? {context.event.external}")
            # aggiornamento dello stato del sistema
            context.network.state.update((job_server_int, job_class), True)

            # generazione evento di departure per il job corrente
            service_rate = context.network.nodes[job_server_int].service_rate[job_class]
            service_time = context.event.node.server.get_service([service_rate])
            queue_time = context.event.node.queue.get_queue_time()
            departure_time = service_time + queue_time

            context.event.job.class_id = job_class+1 if job_server != 'A' else job_class
            departure = DepartureEvent(departure_time, HandleDeparture(), context.event.job, context.event.node)
            departure.external = True if (job_server == 'A' and job_class == 2) else False

            # scheduling dell'evento di departure
            context.scheduler.schedule(departure)

            # rigenerazione evento di arrival dall'esterno del sistema
            if context.event.node.id == 'A' and job_class == 0:
                arrival_time = context.network.get_arrivals()
                new_job = Job(0, context.event.job.job_id+1)
                arrival = ArrivalEvent(context.event.time + arrival_time, HandleArrival(), new_job, context.event.node)
                arrival.external = True
                context.scheduler.schedule(arrival)
        

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
        