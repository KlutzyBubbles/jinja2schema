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