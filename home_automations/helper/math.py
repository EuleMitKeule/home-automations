from abc import ABC


class Math(ABC):
    @classmethod
    def lerp(cls, from_value: float, to_value: float, t: float) -> float:
        return from_value * t + to_value * (1 - t)

    @classmethod
    def round_to_nearest_half(cls, value: float) -> float:
        return round(value * 2) / 2
