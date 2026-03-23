from fretboard.music.scales import Scale



def calculate_fret_positions(
    scale: Scale,
    scale_length: float,
    num_frets: int,
    tuning_offset: int = 0,
) -> list[float]:
    frets = []
    steps = scale.steps
    tones = len(steps) - 1

    for fret in range(num_frets + 1):
        if fret == 0:
            frets.append(0.0)
            continue

        index = ((tuning_offset + fret - 1) % tones) + 1
        previous = steps[index - 1]
        current = steps[index]
        ratio = 1 - ((current[1] * previous[0]) / (current[0] * previous[1]))
        distance = frets[-1] + (scale_length - frets[-1]) * ratio
        frets.append(distance)

    return frets
