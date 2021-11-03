import os
import jinja2schema
import ansible.plugins.filter.core
import ansible.plugins.filter.mathstuff
import ansible.plugins.filter.urls
import ansible.plugins.filter.urlsplit
import jinja2schema

filters = [
  ansible.plugins.filter.core.FilterModule(),
  ansible.plugins.filter.mathstuff.FilterModule(),
  ansible.plugins.filter.urls.FilterModule(),
  ansible.plugins.filter.urlsplit.FilterModule()
]

config = jinja2schema.Config(CUSTOM_FILTERS=filters)

def find_in_folder(folder):
  for root, dirs, files in os.walk(folder):
    for dir in dirs:
      find_in_folder(os.path.join(folder, dir))
    for file in files:
      if file.endswith('.txt'):
        with open(os.path.join(folder, file), 'r') as f:
          data = f.read()
          print('-------------')
          print('DATA')
          print(data)
          variables = jinja2schema.infer(data, config)
          print('VARIABLES')
          print(variables)
          print('-------------')
    break

find_in_folder('/home/klutzybubbles/jinja2schema/tests/ansible-check/cases')