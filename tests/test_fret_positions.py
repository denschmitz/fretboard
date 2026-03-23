from fretboard.music.fret_positions import calculate_fret_positions
from fretboard.music.scales import equal_temperament



def test_equal_temperament_starts_at_zero() -> None:
    positions = calculate_fret_positions(equal_temperament(), 25.5, 22)
    assert positions[0] == 0.0
    assert positions[1] > 0.0
    assert positions[-1] < 25.5
