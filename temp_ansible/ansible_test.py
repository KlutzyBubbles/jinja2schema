#!/usr/bin/python

from ansible.parsing.dataloader import DataLoader
from ansible.playbook import Playbook
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from pprint import pprint
from ansible.playbook.block import Block
from ansible.utils.sentinel import Sentinel
import jinja2
from jinja2 import Environment, PackageLoader, meta
import ansible.plugins.filter.core
import ansible.plugins.filter.mathstuff
import ansible.plugins.filter.urls
import ansible.plugins.filter.urlsplit
import jinja2schema
from ansible import constants as C
from scope.scope import Scope
from scope.error_record import ErrorRecord
from ansible.playbook.task_include import TaskInclude
from ansible.playbook.role_include import IncludeRole
from ansible.playbook.role.include import RoleInclude
from ansible.playbook.role import Role

loader = DataLoader()
loader.set_basedir('.')

filters = [
  ansible.plugins.filter.core.FilterModule(),
  ansible.plugins.filter.mathstuff.FilterModule(),
  ansible.plugins.filter.urls.FilterModule(),
  ansible.plugins.filter.urlsplit.FilterModule()
]
config = jinja2schema.Config(CUSTOM_FILTERS=filters)

inventory = InventoryManager(loader=loader, sources=None)

# create the variable manager, which will be shared throughout
# the code, ensuring a consistent view of global variables
variable_manager = VariableManager(loader=loader, inventory=inventory)
# ds = dl.load_from_file('./deploy_sap_set.yml')

# print(ds)

class YamlConstructor(object):

  def __init__(self, new_line='\n', tab='  '):
    super(YamlConstructor, self).__init__()
    self.new_line = new_line
    self.tab = tab

  def to_string(self, dict_val, current_string='', current_tab=''):
    if not isinstance(dict_val, dict):
      return 'Invalid dict_val'
    string = current_string
    for key, value in dict_val.items():
      string += current_tab + key
      if isinstance(value, dict):
        if not len(value.keys()) == 0:
          string += ':' + self.new_line
          string = self.to_string(value, current_string=string, current_tab=current_tab + self.tab)
          continue
      if isinstance(value, list) or isinstance(value, tuple):
        string += ':' + self.new_line
        for item in value:
          string += current_tab + self.tab + '- ' + str(item) + self.new_line
        continue
      string += ': \'\'' + self.new_line
    return string

playbook = Playbook(loader)

test = playbook.load('./deploy_sap_set.yml', loader=loader, variable_manager=variable_manager)
pprint(test)

properties = [
  'failed_when',
  'loop',
  'loop_with',
  'name',
  'tags',
  'until',
  'when',
  'no_log',
  'ignore_errors',
  'check_mode',
  'changed_when',
  'become',
  'become_method',
  'become_flags',
  'become_user'
]

no_block = [
  'when',
  'failed_when',
  'changed_when'
]

ignored = [
  'action',
  'notify',
  'loop_control'
]

jinja_errors = []

def get_vars(string, task, play, other_scope=None):
  try:
    variables = jinja2schema.infer(string, config)
    return variables
  except Exception, e:
    task_role = task._role if task is not None else None
    jinja_errors.append(ErrorRecord(str(e), task, play, test, role=task_role, other_scope=other_scope))
    return {}

def add_vars(scope, variables, action, trail=[], debug=False):
  if 'default_deployment_item' in variables.keys():
    debug = True
  if debug:
    print('DEBUG MODE')
    print('trail ' + str(trail))
    for key, value in variables.items():
      print(type(value))
      if isinstance(value, jinja2schema.model.Dictionary) or isinstance(value, dict):
        print('IS INSTANCE')
        temp = list(trail)
        temp.append(key)
        add_vars(scope, value, action, trail=temp, debug=debug)
      else:
        if len(trail) == 0:
          print('ADDING NORMAL')
          scope.add_variable(key, action)
        else:
          print ('ADDING with trail')
          temp = list(trail)
          temp.append(key)
          scope.add_attribute(temp.pop(0), temp, action)
    return scope
  else:
    for key, value in variables.items():
      if isinstance(value, jinja2schema.model.Dictionary) or isinstance(value, dict):
        temp = list(trail)
        temp.append(key)
        add_vars(scope, value, action, trail=temp)
      else:
        if len(trail) == 0:
          scope.add_variable(key, action)
        else:
          temp = list(trail)
          temp.append(key)
          scope.add_attribute(temp.pop(0), temp, action)
    return scope

def add_used_vars(scope, variables, trail=[], debug=False):
  add_vars(scope, variables, 'used', trail=trail, debug=debug)

scopes = {}
errors = []

def process_block(scope, block, play):
  for task in block:
    #print(task._role)
    #if task._attributes['name'] is Sentinel:
      #pprint(vars(task))
      # pprint(vars(task._role))
      # print('LAODER')
      # pprint(vars(task._role._loader).keys())
      # print('METADATA')
      # pprint(vars(task._role._metadata))
    action = task._attributes['action'] if 'action' in task._attributes else 'unknown'
    task_scope = scope
    if 'loop_control' in task._attributes and task._attributes['loop_control'] is not Sentinel:
      task_scope = scope.create_child()
      task_scope.add_variable(task._attributes['loop_control'].loop_var, 'registered')
    elif 'loop' in task._attributes and task._attributes['loop'] is not Sentinel:
      task_scope = scope.create_child()
      task_scope.add_variable('item', 'registered')
    elif 'loop_with' in task._attributes and task._attributes['loop_with'] is not Sentinel:
      task_scope = scope.create_child()
      task_scope.add_variable('item', 'registered')
    process_task_attr(task_scope, task, play)
    if action in C._ACTION_ALL_PROPER_INCLUDE_IMPORT_TASKS:
      t = TaskInclude(block=block)
      process_task_attr(task_scope, t, play)
    elif action in C._ACTION_ALL_PROPER_INCLUDE_IMPORT_ROLES:
      ri = RoleInclude.load(task._role_name, play=play, variable_manager=variable_manager)
      r = Role.load(ri, play)
      for block in r.compile(play):
        if block.has_tasks():
          process_block(scope, block.block, play)
    elif action in C._ACTION_IMPORT_PLAYBOOK:
      errors.append(ErrorRecord('Playbook include not implemented yet', task, play, test, role=task._role))
    elif action in C._ACTION_INCLUDE_VARS:
      errors.append(ErrorRecord('Var include not implemented yet', task, play, test, role=task._role))
    elif action in C._ACTION_INCLUDE:
      errors.append(ErrorRecord('Includes not supported', task, play, test, role=task._role))

def process_task_attr(task_scope, task, play):
  # pprint(vars(task))
  for attr, attr_value in task._attributes.items():
    if attr_value is not None and attr_value is not Sentinel:
      if attr == 'vars':
        for var, var_val in attr_value.items():
          add_used_vars(task_scope, get_vars(var_val, task, play))
      elif attr in properties:
        if isinstance(attr_value, list) or isinstance(attr_value, tuple):
          for attr_item in attr_value:
            if attr in no_block:
              attr_item = '{{ ' + str(attr_item) + ' }}'
            add_used_vars(task_scope, get_vars(attr_item, task, play))
        else:
          if attr in no_block:
            attr_value = '{{ ' + str(attr_value) + ' }}'
          add_used_vars(task_scope, get_vars(attr_value, task, play))
      elif attr in ['block', 'rescue', 'always']:
        process_block(task_scope, attr_value, play)
      elif attr == 'args':
        action = task._attributes['action'] if 'action' in task._attributes else 'unknown'
        if action == 'set_fact':
          process_set_fact_args(task_scope, attr_value, task, play)
        else:
          process_args(task_scope, attr_value, task, play)
      elif attr == 'register':
        task_scope.add_variable(attr_value, 'registered')
      elif attr not in ignored:
        errors.append(ErrorRecord('Unknown attr, ' + attr, task, play, test, role=task._role))

def process_args(scope, args, task, play, other_scope=None, action='used'):
  for arg, arg_value in args.items():
    if isinstance(arg_value, dict):
      process_args(scope, arg_value, task, play, action=action)
    if isinstance(arg_value, list):
      for item in arg_value:
        add_vars(scope, get_vars(item, task, play, other_scope=other_scope), action)
    elif isinstance(arg_value, str):
      add_vars(scope, get_vars(arg_value, task, play, other_scope=other_scope), action)

def process_set_fact_args(scope, args, task, play, other_scope=None, trail=[]):
  for arg, arg_value in args.items():
    if isinstance(arg_value, dict):
      temp = list(trail)
      temp.append(arg)
      process_set_fact_args(scope, arg_value, task, play, trail=temp)
    else:
      if isinstance(arg_value, list):
        for item in arg_value:
          add_vars(scope, get_vars(item, task, play, other_scope=other_scope), 'used')
      elif isinstance(arg_value, str):
        add_vars(scope, get_vars(arg_value, task, play, other_scope=other_scope), 'used')
      if len(trail) == 0:
        scope.add_variable(arg, 'changed')
      else:
        temp = list(trail)
        temp.append(arg)
        scope.add_attribute(temp.pop(0), temp, 'changed')

print(vars(test._loader).keys())
print(vars(loader).keys())
for play in test.get_plays():
  # print ('----- PLAY -----')
  # print (play.get_name())
  # print(vars(play).keys())
  if play.get_name() not in scopes:
    scopes[play.get_name()] = Scope()
  scope = scopes[play.get_name()]
  for var in play.get_vars():
    # if var == 'unique_name_token':
    #   # print('=== unique_name_token ===')
    #   # pprint(get_vars(play.vars[var]))
    #   yaml_constructor = YamlConstructor()
    #   print(yaml_constructor.to_string(scope.get_all()))
    #   add_used_vars(scope, get_vars(play.vars[var]), debug=True)
    #   print(yaml_constructor.to_string(scope.get_all()))
    # else:
      add_used_vars(scope, get_vars(play.vars[var], None, play, other_scope='play var, ' + str(var)))
  for var in play.get_vars():
    scope.add_variable(var, 'changed')
  flush_block = Block.load(
      data={'meta': 'flush_handlers'},
      play=play,
      variable_manager=play._variable_manager,
      loader=play._loader
  )

  for task in flush_block.block:
      task.implicit = True

  block_list = []

  block_list.extend(play.pre_tasks)
  block_list.append(flush_block)

  if len(play.roles) > 0:
    for role in play.roles:
      # pprint(vars(role))
      # print(role._role_name)
      process_set_fact_args(scope, role.get_default_vars(), None, play, other_scope='role default vars')
      process_set_fact_args(scope, role.get_vars(), None, play, other_scope='role vars')

  block_list.extend(play._compile_roles())
  block_list.extend(play.tasks)
  block_list.append(flush_block)
  block_list.extend(play.post_tasks)
  block_list.append(flush_block)
  for block in block_list:
    if block.has_tasks():
      process_block(scope, block.block, play)

yaml_constructor = YamlConstructor()

for key in scopes.keys():
  print ('SCOPE - ' + key)
  #print (scopes[key])
  print (yaml_constructor.to_string(scopes[key].get_undefined(with_history=True)))
  # print ('=== ALL ===')
  # print (scopes[key].get_debug())
  # print (yaml_constructor.to_string(scopes[key].get_debug()))

# print('--- JINJA ERRORS ---')
# for error in jinja_errors:
#   print(str(error))

print('--- NORMAL ERRORS ---')
for error in errors:
  print(str(error))

# for item in test._entries:
#   print(item)

# print(test)
# pprint(vars(test))
# pprint(vars(test.get_loader()))
