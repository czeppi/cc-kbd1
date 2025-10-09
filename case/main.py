from finger_parts_new import SkeletonCreator
from case.finger_parts_new import SwitchPairHolderCreator
from case.trackball_holder_new import TrackballHolderCreator
from ocp_vscode import show
from base import OUTPUT_DPATH


def main():
    #SkeletonCreator().create()

    #holder = SwitchPairHolderCreator().create(OUTPUT_DPATH)
    #show(holder)

    trackball_holder = TrackballHolderCreator().create()
    show(trackball_holder)


main()