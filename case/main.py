from keys_holder import SkeletonSplineFinder
from hot_swap_socket import SwitchPairHolderCreator
from ocp_vscode import show_object
from base import OUTPUT_DPATH


def main():
    SkeletonSplineFinder().find_path()

    #holder = SwitchPairHolderCreator().create(OUTPUT_DPATH)
    #show_object(holder)


main()