from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class Announcement:
    id: str
    name: str
    link: str
    timestamp: int
    price: float
    image: str | None = None

    def to_message(self) -> str:
        return f"{self.name}\nЦена: {self.price} BYN\n{self.link}"

    def to_dict(self) -> dict:
        return asdict(self)
