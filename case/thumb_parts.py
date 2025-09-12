from trackball_holder_new import TrackballHolderCreator
from ocp_vscode import show_object


def main():
    creator = TrackballHolderCreator()
    holder = creator.create()
    show_object(holder)


if __name__ == '__main__':
    main()