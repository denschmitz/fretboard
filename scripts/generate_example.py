from pprint import pprint

from fretboard.app import build_design_summary, resolve_spec



def main() -> None:
    spec = resolve_spec("gibson_les_paul")
    pprint(build_design_summary(spec))


if __name__ == "__main__":
    main()
