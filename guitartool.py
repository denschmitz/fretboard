import sys

def main():
    if "--gui" in sys.argv:
        import gui
        gui.launch_gui()
    else:
        import cli
        cli.run_cli()

if __name__ == "__main__":
    main()
