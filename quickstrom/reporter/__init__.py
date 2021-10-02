from abc import abstractmethod
from dataclasses import dataclass
from quickstrom.protocol import Result

@dataclass
class Reporter():
    @abstractmethod
    def report(self, result: Result) -> None:
        pass
