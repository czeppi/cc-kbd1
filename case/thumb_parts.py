from trackball_holder import TrackballHolderCreator
from ocp_vscode import show


def main():
    creator = TrackballHolderCreator()
    holder = creator.create()
    show(holder)


if __name__ == '__main__':
    main()