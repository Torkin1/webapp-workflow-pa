from abc import ABC, abstractmethod


class Clonable(ABC):
    @abstractmethod
    def __copy__(self):
        pass