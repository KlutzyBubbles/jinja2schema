import os

class FileHandler(object):

  def __init__(self, *items, **kwargs):
    super(FileHandler, self).__init__()
    self._file = kwargs['file'] if 'file' in kwargs else False
    self._dir = kwargs['dir'] if 'dir' in kwargs else False
    if not self._file and not self._dir:
      self._file = True
    elif self._file and self._dir:
      self._file = False
    self.basedir = kwargs['basedir'] if 'basedir' in kwargs else False
    if self.basedir is None:
      self.basedir = '.'
    if not os.path.isdir(self.basedir):
      raise Exception('Invalid base dir, ' + str(self.basedir))
    self.items = list(items)
    self._constructed = False
    self.construct_valids()

  def _validate_constructed(self):
    if not self._constructed:
      raise Exception('Valids not yet constructed')

  def construct_valids(self):
    self.dirs = {}
    self.files = {}
    if self._file:
      for item in self.items:
        path = os.path.join(self.basedir, item)
        if os.path.isfile(path):
          self.files[path] = True
        else:
          self.files[path] = False
    elif self._dir:
      for item in self.items:
        path = os.path.join(self.basedir, item)
        if os.path.isdir(path):
          self.dirs[path] = True
          for (_path, _dirnames, filenames) in os.walk(path):
            for filename in filenames:
              self.files[os.path.join(path, filename)] = True
            break
        else:
          self.dirs[path] = False
    else:
      raise Exception('Invalid combination of _file and _dir')
    self._constructed = True

  def get_valid_files(self):
    return [filename for filename in self.files.keys() if self.files[filename]]

  def get_valid_dirs(self):
    return [dirname for dirname in self.dirs.keys() if self.dirs[dirname]]

