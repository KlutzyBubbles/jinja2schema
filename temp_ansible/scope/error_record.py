from ansible.utils.sentinel import Sentinel

class ErrorRecord(object):

  def __init__(self, message, task, play, playbook, role=None, other_scope=None):
    super(ErrorRecord, self).__init__()
    self.message = message
    self.task = task
    self.play = play
    self.playbook = playbook
    self.role = role
    self.other_scope = other_scope

  def construct_scope(self):
    scope_string = '[pb]' + self.playbook._file_name + '->'
    play_name = self.play._attributes['hosts'] if 'hosts' in self.play._attributes else 'unknown'
    if 'name' in self.play._attributes and self.play._attributes['name'] is not Sentinel:
      play_name = self.play._attributes['name']
    scope_string += '[p]' + play_name + '->'
    if self.role is not None:
      scope_string += '[r]' + self.role._role_name + '->'
    if self.task is not None:
      task_action = self.task._attributes['action'] if 'action' in self.task._attributes else 'unknown'
      task_name = task_action
      if 'name' in self.task._attributes and self.task._attributes['name'] is not Sentinel:
        task_name = self.task._attributes['name'] + '(' + task_action + ')'
      scope_string += '[t]' + task_name
    if self.other_scope is not None:
      scope_string += '[o]' + str(self.other_scope)
    return scope_string

  def __repr__(self):
    return self.construct_scope() + ': ' + str(self.message)
