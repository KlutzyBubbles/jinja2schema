from inspect import getargspec, ismethod
from pprint import pprint

def func(self, test, testint=1, teststr=''):
  return None

argspec = getargspec(func)
args = getargspec(func).args

pprint(argspec)
