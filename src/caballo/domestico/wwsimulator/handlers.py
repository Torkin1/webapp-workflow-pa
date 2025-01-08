from caballo.domestico.wwsimulator.events import EventContext, EventHandler, Event, ArrivalEvent, DepartureEvent, MisurationEvent
from caballo.domestico.wwsimulator.model import Job, PSQueue
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


class HandleArrival(EventHandler):
    
    class State:
        def __init__(self):
            self.scheduled_departures = []
    
    def __init__(self):
        super().__init__()
        self.state_by_node = {}

    def _remove_expired_departures(self, now, state):
        state.scheduled_departures = [departure for departure in state.scheduled_departures if departure.time >= now and not departure.is_cancelled]
        

    def _update_departures(self, now, state, num_jobs_in_service, scheduler):
        
        # remove departures with time strictly in the past.
        #
        # This means that departures with time == now are updated, but they could have
        # already been processed. This is not a problem since the num_jobs_in_service
        # is calculated using state, which reflects the true value of jobs in service
        # at this note.
        # 
        # The worst that can happen is that already processed departures
        # have their time updated, but they have already been remove from event queue
        # so their update is silently ignored by the simulation.
        self._remove_expired_departures(now, state)
        
        # La pesca random è sul tempo di servizio, che chiamiamo S. 
        # Sia Srem il tempo di servizio rimanente.
        # Sia Drem la domanda rimanente e mu il rate di servizio, allora Srem = Drem/mu.
        # Prendiamo nuovo rate mu2 = mu/N, dove N è il numero dei job in servizio.
        # Sia Srem2 = Drem/mu2 il tempo di servizio che ci metterebbe con mu2.
        # Ti ricavi Drem = Srem•mu => Srem2 = (Srem•mu)/(mu/N) = Srem • N
        # Ora i job vanno schedulati a current time + Srem2
        scheduled_departures = state.scheduled_departures
        for departure in scheduled_departures:

            # cancel old departures and schedules a new one after recalculating the remaining service time
            scheduler.cancel(departure)
            remaining_service_time = (departure.time - now) * num_jobs_in_service
            departure_time = now + remaining_service_time
            new_departure = DepartureEvent(departure_time, HandleDeparture(), departure.job, departure.node)
            new_departure.external = departure.external
            scheduler.schedule(new_departure)

    
    def _handle(self, context: EventContext):
        
        job_class = context.event.job.class_id

        job_server = context.event.node.id
        job_server_int = context.event.node.node_map(job_server)
        # aggiornamento dello stato del sistema
        context.network.state.update((job_server_int, job_class), True)

        # generazione evento di departure per il job corrente
        service_rate = context.network.nodes[job_server_int].service_rate[job_class]
        
        # rescale service rate if we are using a PS node
        node = context.event.node
        if type(node.queue) is PSQueue:

            if node not in self.state_by_node:
                self.state_by_node[node.id] = HandleArrival.State()
            state = self.state_by_node[node.id]
                        
            # calc num jobs in service using state.
            # !NOTE: Do not use the scheduled departures count!
            # we cannot know if departures with time == now have already been processed.
            node_index = context.event.node.node_map(node.id)
            num_jobs_in_node = sum(context.network.state.get_node_state(node_index))

            # update departure times for already scheduled jobs
            now = context.event.time
            self._update_departures(now, state, num_jobs_in_node, context.scheduler)


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
            self.state_by_node[node.id].scheduled_departures.append(departure)        

class HandleDeparture(EventHandler):
    def __init__(self):
        super().__init__()

    def _handle(self, context: EventContext):
        job_server_str = context.event.node.id
        job_server = context.event.node.node_map(job_server_str)
        job_class = context.event.job.class_id
    
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
        job = Job(0, 0, 0)
        node = context.network.nodes[0]
        arrival = ArrivalEvent(0.0, HandleArrival(), job, node)
        arrival.external = True
        context.scheduler.schedule(arrival)
        