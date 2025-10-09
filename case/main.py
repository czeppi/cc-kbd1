from finger_parts import SkeletonCreator
from finger_parts import SwitchPairHolderCreator
from trackball_holder import TrackballHolderCreator
from ocp_vscode import show
from base import OUTPUT_DPATH


def main():
    #SkeletonCreator().create()

    #holder = SwitchPairHolderCreator().create(OUTPUT_DPATH)
    #show(holder)

    trackball_holder = TrackballHolderCreator().create()
    show(trackball_holder)


main()