class Job():
    """
    A unit of work to be processed by the nodes in a simulation.
    """
    def __init__(self, class_id: str, job_id: int):
        self._class_id = class_id
        self._job_id = job_id
        @property
        def class_id(self):
            return self._class_id

        @class_id.setter
        def class_id(self, value):
            self._class_id = value

        @property
        def job_id(self):
            return self._job_id
    
# TODO: this is a mock
class Network:
    pass

# TODO: this is a mock
class Server:
    pass

# TODO: this is a mock
class State:
    pass


