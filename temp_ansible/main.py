import argparse

parser = argparse.ArgumentParser(description='Process ansible files to get variable information')

parser.add_argument('items', metavar='item', type=str, nargs='+',
                    help='File(s) or folder(s) to use as the input')
parser.add_argument('-v', '--verbosity', action='count',
                    help='Verbosity of output')
type_group = parser.add_mutually_exclusive_group()
type_group.add_argument('-d', '--dir', action='store_true',
                    help='Indicate the input(s) are directories')
type_group.add_argument('-f', '--file', action='store_true',
                    help='Indicate the input(s) are files')

args = parser.parse_args()
print(args)