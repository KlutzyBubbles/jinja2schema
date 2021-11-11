import logging

try:
  import textwrap
  textwrap.indent
except AttributeError:
  def indent(text, amount, ch=' '):
    padding = amount * ch
    return ''.join(padding+line for line in text.splitlines(True))
else:
  def indent(text, amount, ch=' '):
    return textwrap.indent(text, amount * ch)

class IndentedLoggerAdapter(logging.LoggerAdapter):

  def __init__(self, logger, extra=None, num_per_indent=2, char=None):
    super(IndentedLoggerAdapter, self).__init__(logger, extra)
    self.num_per_indent = num_per_indent
    self.indent = 0
    self.filo = []
    self.char = char if char is not None else ' '

  def _add_to_filo(self, value):
    self.history.insert(0, value)
    self.history.pop()

  def _pop_recent_history(self):
    self.history.append(None)
    return self.history.pop(0)

  def adjust(self, adjust=0):
    if adjust == 0:
      return
    self.indent += adjust
    if self.indent < 0:
      self.indent = 0
    return self

  def add(self, amount=1):
    self.adjust(amount)
    return self

  def sub(self, amount=1):
    self.adjust(-1 * amount)
    return self

  def push(self, indent=None):
    new_indent = indent
    if new_indent is None:
      new_indent = self.indent
    self.filo.append(new_indent)
    return self

  def pop(self):
    if len(self.filo) > 0:
      self.indent = self.filo.pop()
    return self

  def calc_indent(self):
    temp = self.char * (self.num_per_indent * self.indent)
    return temp

  def process(self, msg, kwargs):
    msg = indent(msg, self.indent, ch=self.char * self.num_per_indent)
    return msg, kwargs
