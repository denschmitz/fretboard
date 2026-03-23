class Scale:
    def __init__(self) -> None:
        self.steps = [(1, 1)]
        self.title = ""
        self.errors: list[str] = []

    def add_step(self, numerator: float, denominator: float) -> None:
        self.steps.append((numerator, denominator))

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def from_equal_temperament(self, tones: int, octave: float = 2.0) -> "Scale":
        if tones <= 0:
            self.add_error("Number of tones must be greater than zero")
            return self

        self.title = f"{tones}-EDO"
        for step_index in range(1, tones + 1):
            ratio = octave ** (step_index / tones)
            self.add_step(ratio, 1)
        return self

    def from_scala_string(self, scala_string: str) -> "Scale":
        lines = [
            line.strip()
            for line in scala_string.splitlines()
            if line.strip() and not line.startswith("!")
        ]
        if not lines:
            self.add_error("Empty or invalid Scala file")
            return self

        self.title = lines[0]
        try:
            expected = int(lines[1])
        except ValueError:
            self.add_error("Invalid tone count line")
            return self

        for line in lines[2 : 2 + expected]:
            if "." in line:
                cents = float(line)
                ratio = 2 ** (cents / 1200)
                self.add_step(ratio, 1)
            elif "/" in line:
                numerator, denominator = map(int, line.split("/"))
                self.add_step(numerator, denominator)
            else:
                self.add_step(int(line), 1)

        if len(self.steps) - 1 != expected:
            self.add_error(f"Expected {expected} steps, found {len(self.steps) - 1}")

        return self



def equal_temperament(tones: int = 12, octave: float = 2.0) -> Scale:
    return Scale().from_equal_temperament(tones, octave)
