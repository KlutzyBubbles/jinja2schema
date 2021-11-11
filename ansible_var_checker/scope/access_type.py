import pprint

ACCESS_TYPE_USED = 'used'
ACCESS_TYPE_REFERENCED = 'referenced'
ACCESS_TYPE_MAGIC = 'magic'
ACCESS_TYPE_CHANGED = 'changed'
ACCESS_TYPE_REGISTERED = 'registered'
ACCESS_TYPE_BUILT = 'built'

ACCESS_TYPE_PROPER_DEFINED = [ACCESS_TYPE_CHANGED, ACCESS_TYPE_REGISTERED, ACCESS_TYPE_BUILT]
ACCESS_TYPE_USED_REFERENCED = [ACCESS_TYPE_USED, ACCESS_TYPE_REFERENCED]
ACCESS_TYPE_ALL = ACCESS_TYPE_PROPER_DEFINED + ACCESS_TYPE_USED_REFERENCED + [ACCESS_TYPE_MAGIC]

class AccessType(object):

  def __init__(self):
    self.actions = []
    self.attributes = {}
    self.indexes = {}

  def __repr__(self):
    output = {}
    output['actions'] = pprint.pformat(self.actions)
    output['attributes'] = pprint.pformat(self.attributes)
    output['indexes'] = pprint.pformat(self.indexes)
    return pprint.pformat(output)

  @staticmethod
  def validate_action(action):
    if action not in ACCESS_TYPE_ALL:
      raise Exception('Invalid action ' + str(action))

  def has_attr(self):
    return len(self.attributes.keys()) > 0

  def is_undefined(self):
    if len(self.actions) == 0:
      return True
    return self.actions[0] in ACCESS_TYPE_USED_REFERENCED

  def is_magic(self):
    if len(self.actions) == 0:
      return False
    return self.actions[0] in [ACCESS_TYPE_MAGIC]

  def is_magic_used(self):
    if len(self.actions) == 0:
      return False
    has_used = False
    if self.actions[0] in [ACCESS_TYPE_MAGIC]:
      temp_actions = list(self.actions)
      temp_actions.pop(0)
      for action in temp_actions:
        if action in ACCESS_TYPE_USED_REFERENCED:
          has_used = True
          break
    return has_used

  def construct_from_attr(self, with_history=False):
    if not self.has_attr():
      return {} if not with_history else self.actions
    output = {}
    if with_history:
      output['_actions'] = self.actions
    for key, value in self.attributes.items():
      output[key] = value.construct_from_attr(with_history=with_history)
    return output

  def add(self, action, count=1):
    for i in range(count):
      self.actions.append(action)

  def add_registered(self, count=1):
    self.add(ACCESS_TYPE_REGISTERED, count=count)

  def add_changed(self, count=1):
    self.add(ACCESS_TYPE_CHANGED, count=count)

  def add_magic(self, count=1):
    self.add(ACCESS_TYPE_MAGIC, count=count)

  def add_used(self, count=1):
    self.add(ACCESS_TYPE_USED, count=count)

  def add_referenced(self, count=1):
    self.add(ACCESS_TYPE_REFERENCED, count=count)

  def add_attribute(self, attribute, action, count=1):
    AccessType.validate_action(action)
    if isinstance(attribute, list):
      attribute_item = attribute.pop(0)
    else:
      attribute_item = attribute
      attribute = []
    action_params = {}
    action_params[action] = count
    if attribute_item not in self.attributes:
      self.attributes[attribute_item] = AccessType()
    if len(attribute) == 0:
      self.attributes[attribute_item].add(action, count=count)
    else:
      self.attributes[attribute_item].add_attribute(attribute, action, count=count)

  def add_indexed(self, index, action, count=1):
    AccessType.validate_action(action)
    if isinstance(index, list):
      index_item = index.pop(0)
    else:
      index_item = index
      index = []
    action_params = {}
    action_params[action] = count
    if index_item not in self.attributes:
      self.indexes[index_item] = AccessType()
    if len(index) == 0:
      self.indexes[index_item].add(action, count=count)
    else:
      self.indexes[index_item].add_indexed(index, action, count=count)
