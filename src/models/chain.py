from dataclasses import dataclass
from typing import Optional

@dataclass
class Chain:
    """Represents a blockchain network."""
    id: str
    name: str
    native_token: str
    wrapped_native: str
    rpc_url: Optional[str] = None

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Chain):
            return self.id == other.id
        return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Chain(name={self.name}, id={self.id})"