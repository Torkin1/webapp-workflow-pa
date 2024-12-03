error = 'index out of range'
class Job():
    """
    A unit of work to be processed by the nodes in a simulation.
    """
    def __init__(self, class_id: int, job_id: int):
        self.class_id = class_id
        self.job_id = job_id

    def class_id(self):
        return self.class_id

    def class_id(self, value):
        self.class_id = value

    def job_id(self):
        return self.job_id
    

class State:
    """
    Classe che definisce lo stato del sistema con una matrice 3x3 
    dove ogni riga rappresenta un nodo e ogni colonna una classe di job
    """
    def __init__(self, matrix):
        self.matrix = matrix

    def update(self, node_class: tuple, increment: bool):
        """
        Metodo per incrementare o decrementare lo stato di un nodo
        """

        if node_class[1] > 3 or node_class[0] > 3:
            raise ValueError(error)
        
        self.matrix[node_class[0]][node_class[1]] += 1 if increment else -1

    def get(self):
        """
        Metodo per ritornare la matrice completa dello stato
        """
        return self.matrix
    
    def get_node_state(self, node):
        """
        Metodo per ritornare lo stato di un singolo nodo
        """
        return self.matrix[node]
    
    def get_total_class(self, class_type):
        """
        Metodo per ritornare il numero totale di job in una certa classe nel sistema
        """
        if class_type > 3:
            raise ValueError(error)
        return sum([self.matrix[i][class_type] for i in range(3)])
    
class Server():
    """
    Classe che definisce un server all'interno di un nodo. Il server ha una capacità
    e una distribuzione di servizio.
    id: identificativo del server, può essere A, B, P
    capacity: capacità del server
    server_distribution: tupla con distribuzione di servizio e parametro della distribuzione
    """
    def __init__(self, id: str, capacity: int, server_distribution: str):
        self.id = id
        self.capacity = capacity
        self.server_distribution = server_distribution

    def node_map(self, node_id):
        server_map = {'A': 0, 'B': 1, 'P': 2}
        if node_id not in server_map:
            raise ValueError(error)
        return server_map[node_id]
        
class Queue():
    def __init__(self, capacity: int, queue_policy='FIFO'):
        self.id = id
        self.capacity = capacity
        self.queue_policy = queue_policy

class Node:
    def __init__(self, id: str, service_rate: list, server:Server, queue:Queue):
        self.id = id
        self.server = server
        self.queue = queue
        self.service_rate = service_rate

    def get_service_class_rate(self, class_type):
        if class_type > 3:
            raise ValueError(error)
        
        return self.service_rate[class_type]


class Network:
    def __init__(self, nodes: list, state: State):
        self.nodes = nodes
        self.state = state

    def get_node(self, node_id):
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_state(self):
        return self.state.get()

    def get_node_state(self, node_id):
        node = self.get_node(node_id)
        return self.state.get_node_state(node.id)

    def get_total_class(self, class_type):
        return self.state.get_total_class(class_type)