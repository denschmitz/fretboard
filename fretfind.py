import math
import re

class Point:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def copy(self):
        return Point(self.x, self.y)

    def midpoint(self, other):
        return Point((self.x + other.x) / 2, (self.y + other.y) / 2)

    def __repr__(self):
        return f"({self.x:.5f}, {self.y:.5f})"

class Segment:
    def __init__(self, end1: Point, end2: Point):
        self.end1 = end1
        self.end2 = end2

    def delta_x(self):
        return self.end2.x - self.end1.x

    def delta_y(self):
        return self.end2.y - self.end1.y

    def length(self):
        return math.hypot(self.delta_x(), self.delta_y())

    def midpoint(self):
        return Point(
            (self.end1.x + self.end2.x) / 2,
            (self.end1.y + self.end2.y) / 2
        )

    def point_at_ratio(self, ratio):
        x = self.end1.x + ratio * self.delta_x()
        y = self.end1.y + ratio * self.delta_y()
        return Point(x, y)

    def intersect(self, other):
        # Intersection of two infinite lines
        x1, y1 = self.end1.x, self.end1.y
        x2, y2 = self.end2.x, self.end2.y
        x3, y3 = other.end1.x, other.end1.y
        x4, y4 = other.end2.x, other.end2.y

        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if denom == 0:
            return None  # Parallel lines

        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
        x = x1 + ua * (x2 - x1)
        y = y1 + ua * (y2 - y1)
        return Point(x, y)

    def __repr__(self):
        return f"{self.end1} -> {self.end2}"

class Scale:
    def __init__(self):
        self.steps = [(1, 1)]  # Implicit root
        self.title = ""
        self.errors = []
    
    def add_step(self, num, denom):
        self.steps.append((num, denom))
    
    def add_error(self, msg):
        self.errors.append(msg)

    def from_equal_temperament(self, tones: int, octave: float = 2.0):
        if tones <= 0:
            self.add_error("Number of tones must be greater than zero")
            return
        self.title = f"{tones}-EDO"
        for i in range(1, tones + 1):
            ratio = octave ** (i / tones)
            self.add_step(ratio, 1)

    def from_scala_string(self, scala_str: str):
        lines = [line.strip() for line in scala_str.splitlines() if line.strip() and not line.startswith('!')]
        if not lines:
            self.add_error("Empty or invalid Scala file")
            return

        self.title = lines[0]
        try:
            expected = int(lines[1])
        except ValueError:
            self.add_error("Invalid tone count line")
            return

        step_lines = lines[2:]
        for line in step_lines[:expected]:
            if '.' in line:
                # Cents
                cents = float(line)
                ratio = 2 ** (cents / 1200)
                self.add_step(ratio, 1)
            elif '/' in line:
                num, denom = map(int, line.split('/'))
                self.add_step(num, denom)
            else:
                num = int(line)
                self.add_step(num, 1)

        if len(self.steps) - 1 != expected:
            self.add_error(f"Expected {expected} steps, found {len(self.steps) - 1}")

def calculate_fret_positions(scale: Scale, scale_length: float, num_frets: int, tuning_offset: int = 0):
    """
    Returns list of fret distances from nut for a single string.
    Supports arbitrary scales (including microtonal).
    """
    frets = []
    steps = scale.steps
    tones = len(steps) - 1

    for fret in range(num_frets + 1):
        if fret == 0:
            frets.append(0.0)
            continue

        i = ((tuning_offset + fret - 1) % tones) + 1
        prev = steps[i - 1]
        curr = steps[i]
        ratio = 1 - ((curr[1] * prev[0]) / (curr[0] * prev[1]))
        distance = frets[-1] + (scale_length - frets[-1]) * ratio
        frets.append(distance)

    return frets

def example_usage():
    print("Testing fret spacing for 12-EDO, 25.5 inch scale")
    scale = Scale()
    scale.from_equal_temperament(12)
    positions = calculate_fret_positions(scale, scale_length=25.5, num_frets=22)
    for i, pos in enumerate(positions):
        print(f"Fret {i:2}: {pos:.5f}\"")

if __name__ == "__main__":
    example_usage()
