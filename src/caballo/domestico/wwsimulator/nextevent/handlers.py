from caballo.domestico.wwsimulator.nextevent.events import EventContext, EventHandler, Event, ArrivalEvent, DepartureEvent
from caballo.domestico.wwsimulator.model import Job, Server
import pdsteele.des.rvgs as des

class HandleArrival(EventHandler):
    def __init__(self):
        super().__init__()

    def _handle(self, context: EventContext):
        job_class = context.event.job.class_id
        job_id = context.event.job.job_id
        job_server = context.event.server.id
        job_server_int = context.event.server.node_map(job_server)
        # TODO: rimuovere limite job
        if job_id < 10:
            print(f"Arrival of job {job_id} of class {job_class} at server {job_server}:{job_server_int}")
            # aggiornamento dello stato del sistema
            context.network.state.update((job_server_int, job_class), True)

            # generazione evento di departure per il job corrente
            service_rate = context.network.nodes[job_server_int].service_rate[job_class]
            service_time = context.event.server.get_service([service_rate])
            # TODO: aggiungere la departure del job precedente al time del job corrente
            departure = DepartureEvent(context.event.time + service_time, HandleDeparture(), context.event.job, context.event.server)

            # scheduling dell'evento di departure
            context.scheduler.schedule(departure)

            # rigenerazione evento di arrival dall'esterno del sistema
            if job_class == 0:
                arrival_time = context.network.get_arrivals()
                new_job = Job(0, context.event.job.job_id+1)
                arrival = ArrivalEvent(context.event.time + arrival_time, HandleArrival(), new_job, context.event.server)
                context.scheduler.schedule(arrival)
        

class HandleDeparture(EventHandler):
    def __init__(self):
        super().__init__()

    def _handle(self, context: EventContext):
        job_server_str = context.event.server.id
        job_server = context.event.server.node_map(job_server_str)
        job_class = context.event.job.class_id
    
        print(f"Departure of job {context.event.job.job_id} of class {job_class} from server {job_server_str}:{job_server}")

        # aggiornamento dello stato del sistema
        context.network.state.update((job_server, job_class), False)

        # generazione evento di arrival successivo
        context.event.job.class_id = job_class+1 if job_server_str != 'A' or job_class != 0 else job_class
        if job_class < 2:
            if job_server_str in ['B', 'P']:
                new_server_id = 'A'
            elif job_server_str == 'A' and job_class == 0:
                new_server_id = 'B'
            else:
                new_server_id = 'P'
            next_server = Server(new_server_id, 100, 'exp')
            arrival = ArrivalEvent(context.event.time, HandleArrival(), context.event.job, next_server)
            context.scheduler.schedule(arrival)
         
        