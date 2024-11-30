from caballo.domestico.wwsimulator.nextevent.events import EventContext, EventHandler

class HandleArrival(EventHandler):
    def __init__(self):
        super().__init__()

    def _handle(self, context: EventContext):
        # TODO: implement arrival handling
        #
        # Example:
        #
        # Arrival job j classe_1 nel server A 	// entrata nel sistema 
        # N_A_1 += 1 
        # Schedula Departure con servizio classe 1 per job j da server A 
        # Schedula Arrival con delay 0 classe 1 per job j+1 in Server A  
        pass

class HandleDeparture(EventHandler):
    def __init__(self):
        super().__init__()

    def _handle(self, context: EventContext):
        # TODO: implement departure handling
        #
        # Example:
        #
        # Departure job j Classe_1 server A 
        # N_A_1 -= 1 
        # Schedula Arrivo con delay A->B  j  in server B 
        pass