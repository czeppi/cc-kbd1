from finger_parts_new import SkeletonCreator2
from case.finger_parts_new import SwitchPairHolderCreator
from ocp_vscode import show_object
from base import OUTPUT_DPATH


def main():
    SkeletonCreator2().create()

    #holder = SwitchPairHolderCreator().create(OUTPUT_DPATH)
    #show_object(holder)


main()