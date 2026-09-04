from dataclasses import dataclass


@dataclass
class Resource:
    variable: str
    resource_type: str
    open_line: int
    closed: bool = False

    def close(self):
        self.closed = True