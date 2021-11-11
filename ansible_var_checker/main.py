import argparse
from info import __version__
from file_handler import FileHandler
import ansible
from jinja import Config
from parser import PlaybookParser
from yaml_constructor import YamlConstructor
import ansible.plugins.filter.core
import ansible.plugins.filter.mathstuff
import ansible.plugins.filter.urls
import ansible.plugins.filter.urlsplit
from logger import IndentedLoggerAdapter
import logging

logging.basicConfig(format='%(message)s', level=logging.DEBUG)

logger = logging.getLogger(__name__)
adapter = IndentedLoggerAdapter(logger)
title_adapter = IndentedLoggerAdapter(logger, char='-')

parser = argparse.ArgumentParser(description='Process ansible files to get variable information')

parser.add_argument('items', metavar='item', type=str, nargs='+', help='File(s) or folder(s) to use as the input')
parser.add_argument('-v', '--verbosity', action='count', default=0, help='Verbosity of output')
parser.add_argument('--version', action='version', version='v' + __version__)
parser.add_argument('-b', '--basedir', help='basedir to construct the paths for files / dirs from')
type_group = parser.add_mutually_exclusive_group()
type_group.add_argument('-d', '--dir', action='store_true', default=False, help='Indicate the input(s) are directories')
type_group.add_argument('-f', '--file', action='store_true', default=False, help='Indicate the input(s) are files')
type_group.add_argument('-l', '--list-history', action='store_true', default=False, help='List history entry in output')
type_group.add_argument('-m', '--magic', action='store_true', default=False, help='Include magic variables that aren\'t used in output')

args = parser.parse_args()

file_handler = FileHandler(*args.items, **vars(args))

filters = [
  ansible.plugins.filter.core.FilterModule(),
  ansible.plugins.filter.mathstuff.FilterModule(),
  ansible.plugins.filter.urls.FilterModule(),
  ansible.plugins.filter.urlsplit.FilterModule()
]
config = Config(CUSTOM_FILTERS=filters)

yaml_constructor = YamlConstructor()

for filename in file_handler.get_valid_files():
  parser = PlaybookParser(filename, basedir=file_handler.basedir, jinja_config=config)
  parser.process()
  title_adapter.info('FILENAME = ' + filename)
  title_adapter.add()
  adapter.add()
  for key in parser.scopes.keys():
    title_adapter.debug ('SCOPE - ' + key)
    title_adapter.add()
    adapter.add()
    title_adapter.debug ('UNDEFINED:')
    adapter.debug (yaml_constructor.to_string(parser.scopes[key].get_undefined(with_history=args.list_history)))
    title_adapter.debug ('ALL:')
    adapter.debug (yaml_constructor.to_string(parser.scopes[key].get_all(with_history=args.list_history)))
    title_adapter.sub()
    adapter.sub()
  if parser.has_errors():
    title_adapter.debug('--- NORMAL ERRORS ---')
    for error in parser.errors:
      adapter.debug(str(error))
  if parser.has_jinja_errors():
    title_adapter.debug('--- JINJA ERRORS ---')
    for error in parser.jinja_errors:
      adapter.debug(str(error))

# print(file_handler._file)
# print(file_handler._dir)
# print(file_handler.files)
# print(file_handler.get_valid_files())
