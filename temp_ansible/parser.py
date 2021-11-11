# import jinja2schema
from scope import ErrorRecord, Scope
from ansible.parsing.dataloader import DataLoader
from ansible.playbook import Playbook
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible import constants as C
from ansible.playbook.task_include import TaskInclude
from ansible.playbook.role.include import RoleInclude
from ansible.playbook.role import Role
from ansible.playbook.block import Block
from ansible.utils.sentinel import Sentinel
import jinja2schema

PROPERTIES = [
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
  'become_user',
  'delegate_to'
]

NO_BLOCK = [
  'when',
  'failed_when',
  'changed_when'
]

IGNORED = [
  'action',
  'notify',
  'loop_control'
]

class PlaybookParser(object):

  scopes = {}
  errors = []
  jinja_errors = []

  basedir = None
  filename = None
  playbook = None
  loader = None
  inventory = None
  variable_manager = None
  current_play = None
  jinja_config = None

  def __init__(self, filename, basedir=None, jinja_config=None):
    super(PlaybookParser, self).__init__()
    if filename is None or not isinstance(filename, str):
      raise Exception('Invalid filename')
    self.filename = filename
    self.basedir = basedir
    if self.basedir is None or not isinstance(basedir, str):
      self.basedir = '.'
    self.jinja_config = jinja_config

  def _reset_vars(self):
    self.scopes = {}
    self.errors = []
    self.jinja_errors = []
    self.loader = DataLoader()
    self.loader.set_basedir(self.basedir)
    self.inventory = InventoryManager(loader=self.loader, sources=None)
    self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
    self.playbook = Playbook.load(self.filename, loader=self.loader, variable_manager=self.variable_manager)

  def _process_play(self, play):
    self.current_play = play
    if play.get_name() not in self.scopes:
      self.scopes[play.get_name()] = Scope()
    scope = self.scopes[play.get_name()]
    # for var in play.get_vars():
    #   self.add_vars(scope, self.get_jinja_vars(play.vars[var], None, other_scope='play var, ' + str(var)), 'used')
    # print(play.get_vars())
    self._process_set_fact_args_jinja(scope, play.get_vars(), None)
    self._process_set_fact_args(scope, play.get_vars(), None)
    # for var in play.get_vars():
    #   self._process_set_fact_args(scope, args, task, other_scope=None, trail=[])
    #   if scope.is_magic(var):
    #     self.errors.append(ErrorRecord('Play var: ' + var + ' is a reserved magic variable', task, self.current_play, self.playbook, role=task._role))
    #   scope.add_variable(var, 'changed')
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
        self._process_set_fact_args_jinja(scope, role.get_default_vars(), None, other_scope='role default vars')
        self._process_set_fact_args(scope, role.get_default_vars(), None, other_scope='role default vars')
        self._process_set_fact_args_jinja(scope, role.get_vars(), None, other_scope='role vars')
        self._process_set_fact_args(scope, role.get_vars(), None, other_scope='role vars')

    block_list.extend(play._compile_roles())
    block_list.extend(play.tasks)
    block_list.append(flush_block)
    block_list.extend(play.post_tasks)
    block_list.append(flush_block)
    for block in block_list:
      if block.has_tasks():
        self._process_block(scope, block.block)

  def _process_block(self, scope, block):
    for task in block:
      action = task._attributes['action'] if 'action' in task._attributes else 'unknown'
      task_scope = scope
      if 'loop_control' in task._attributes and task._attributes['loop_control'] is not Sentinel:
        task_scope = scope.create_child()
        loop_var = task._attributes['loop_control'].loop_var
        if task_scope.is_magic(loop_var):
          self.errors.append(ErrorRecord('Loop var: ' + loop_var + ' is a reserved magic variable', task, self.current_play, self.playbook, role=task._role))
        task_scope.add_variable(loop_var, 'registered')
      elif 'loop' in task._attributes and task._attributes['loop'] is not Sentinel:
        task_scope = scope.create_child()
        task_scope.add_variable('item', 'registered')
      elif 'loop_with' in task._attributes and task._attributes['loop_with'] is not Sentinel:
        task_scope = scope.create_child()
        task_scope.add_variable('item', 'registered')
      self._process_task_attr(task_scope, task)
      if action in C._ACTION_ALL_PROPER_INCLUDE_IMPORT_TASKS:
        t = TaskInclude(block=block)
        self._process_task_attr(task_scope, t)
      elif action in C._ACTION_ALL_PROPER_INCLUDE_IMPORT_ROLES:
        ri = RoleInclude.load(task._role_name, play=self.current_play, variable_manager=variable_manager)
        r = Role.load(ri, self.current_play)
        for block in r.compile(self.current_play):
          if block.has_tasks():
            self._process_block(scope, block.block)
      elif action in C._ACTION_IMPORT_PLAYBOOK:
        self.errors.append(ErrorRecord('Playbook include not implemented yet', task, self.current_play, self.playbook, role=task._role))
      elif action in C._ACTION_INCLUDE_VARS:
        self.errors.append(ErrorRecord('Var include not implemented yet', task, self.current_play, self.playbook, role=task._role))
      elif action in C._ACTION_INCLUDE:
        self.errors.append(ErrorRecord('Includes not supported', task, self.current_play, self.playbook, role=task._role))

  def _process_task_attr(self, task_scope, task):
    for attr, attr_value in task._attributes.items():
      if attr_value is not None and attr_value is not Sentinel:
        if attr == 'vars':
          for var, var_val in attr_value.items():
            self.add_vars(task_scope, self.get_jinja_vars(var_val, task), 'used')
        elif attr in PROPERTIES:
          if isinstance(attr_value, list) or isinstance(attr_value, tuple):
            for attr_item in attr_value:
              if attr in NO_BLOCK:
                attr_item = '{{ ' + str(attr_item) + ' }}'
              self.add_vars(task_scope, self.get_jinja_vars(attr_item, task), 'used')
          else:
            if attr in NO_BLOCK:
              attr_value = '{{ ' + str(attr_value) + ' }}'
            self.add_vars(task_scope, self.get_jinja_vars(attr_value, task), 'used')
        elif attr in ['block', 'rescue', 'always']:
          self._process_block(task_scope, attr_value)
        elif attr == 'args':
          action = task._attributes['action'] if 'action' in task._attributes else 'unknown'
          if action == 'set_fact':
            self._process_set_fact_args_jinja(task_scope, attr_value, task)
            self._process_set_fact_args(task_scope, attr_value, task)
          else:
            self._process_args(task_scope, attr_value, task)
        elif attr == 'register':
          if task_scope.is_magic(attr_value):
            self.errors.append(ErrorRecord('Registered var: ' + attr_value + ' is a reserved magic variable', task, self.current_play, self.playbook, role=task._role))
          task_scope.add_variable(attr_value, 'registered')
        elif attr not in IGNORED:
          self.errors.append(ErrorRecord('Unknown attr, ' + attr, task, self.current_play, self.playbook, role=task._role))

  def _process_args(self, scope, args, task, other_scope=None, action='used'):
    for arg, arg_value in args.items():
      if isinstance(arg_value, dict):
        self._process_args(scope, arg_value, task, action=action)
      if isinstance(arg_value, list):
        for item in arg_value:
          self.add_vars(scope, self.get_jinja_vars(item, task, other_scope=other_scope), action)
      elif isinstance(arg_value, str):
        self.add_vars(scope, self.get_jinja_vars(arg_value, task, other_scope=other_scope), action)

  def _process_set_fact_args_jinja(self, scope, args, task, other_scope=None, trail=[]):
    for arg, arg_value in args.items():
      if isinstance(arg_value, dict):
        temp = list(trail)
        temp.append(arg)
        self._process_set_fact_args_jinja(scope, arg_value, task, trail=temp)
      else:
        if isinstance(arg_value, list):
          for item in arg_value:
            self.add_vars(scope, self.get_jinja_vars(item, task, other_scope=other_scope), 'used')
        elif isinstance(arg_value, str):
          self.add_vars(scope, self.get_jinja_vars(arg_value, task, other_scope=other_scope), 'used')

  def _process_set_fact_args(self, scope, args, task, other_scope=None, trail=[]):
    for arg, arg_value in args.items():
      if isinstance(arg_value, dict):
        temp = list(trail)
        temp.append(arg)
        self._process_set_fact_args(scope, arg_value, task, trail=temp)
      else:
        if len(trail) == 0:
          if scope.is_magic(arg):
            self.errors.append(ErrorRecord('Set fact var: ' + arg + ' is a reserved magic variable', task, self.current_play, self.playbook, role=task._role))
          scope.add_variable(arg, 'changed')
        else:
          temp = list(trail)
          temp.append(arg)
          name = temp.pop(0)
          if scope.is_magic(name):
            self.errors.append(ErrorRecord('Set fact var: ' + name + ' is a reserved magic variable', task, self.current_play, self.playbook, role=task._role))
          scope.add_attribute(name, temp, 'changed')

  def process(self):
    self._reset_vars()
    for play in self.playbook.get_plays():
      self._process_play(play)

  def get_jinja_vars(self, string, task, other_scope=None):
    try:
      variables = jinja2schema.infer(string, self.jinja_config)
      return variables
    except Exception as e:
      task_role = task._role if task is not None else None
      self.jinja_errors.append(ErrorRecord(str(e), task, self.current_play, self.playbook, role=task_role, other_scope=other_scope))
      return {}

  def add_vars(self, scope, variables, action, trail=[]):
    for key, value in variables.items():
      # isinstance(value, jinja2schema.model.Dictionary)
      if isinstance(value, jinja2schema.model.Dictionary) or isinstance(value, dict):
        temp = list(trail)
        temp.append(key)
        self.add_vars(scope, value, action, trail=temp)
      else:
        if len(trail) == 0:
          scope.add_variable(key, action)
        else:
          temp = list(trail)
          temp.append(key)
          scope.add_attribute(temp.pop(0), temp, action)
    return scope

  def has_errors(self):
    return len(self.errors) > 0

  def has_jinja_errors(self):
    return len(self.jinja_errors) > 0