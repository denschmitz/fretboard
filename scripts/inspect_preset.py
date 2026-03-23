import argparse
from pprint import pprint

from fretboard.domain.presets import get_preset



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("preset")
    args = parser.parse_args()
    pprint(get_preset(args.preset))


if __name__ == "__main__":
    main()
