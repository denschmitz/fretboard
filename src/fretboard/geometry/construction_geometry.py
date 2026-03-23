from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def midpoint(self, other: "Point") -> "Point":
        return Point((self.x + other.x) / 2, (self.y + other.y) / 2)


@dataclass(frozen=True)
class Segment:
    start: Point
    end: Point

    def delta_x(self) -> float:
        return self.end.x - self.start.x

    def delta_y(self) -> float:
        return self.end.y - self.start.y

    def length(self) -> float:
        return math.hypot(self.delta_x(), self.delta_y())

    def point_at_ratio(self, ratio: float) -> Point:
        return Point(
            self.start.x + ratio * self.delta_x(),
            self.start.y + ratio * self.delta_y(),
        )
