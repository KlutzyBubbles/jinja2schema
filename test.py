#!/usr/bin/python

from pprint import pprint
import jinja2
from jinja2 import Environment, PackageLoader, meta
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
config = jinja2schema.Config(CUSTOM_FILTERS=filters, RAISE_ON_INVALID_FILTER_ARGS=False)

all_vars = []
errors = []

def get_vars(string):
  try:
    # template = jinja2.Template(string)
    # template.globals['context'] = get_context
    # template.globals['callable'] = callable
#
    # context = {'a': 1, 'b': 2, 'c': 3}
#
    # print(template.render(**context))
    # parsed_content = env.parse(string)
    # parsed_content = env.from_string(string)
    # print(parsed_content)
    # undeclared_vars = meta.find_undeclared_variables(parsed_content)
    # all_vars.extend(list(undeclared_vars))
    # return list(undeclared_vars)
    variables = jinja2schema.infer(string, config)
    print(variables)
    all_vars.extend(list(variables))
    return list(variables)
  except Exception, e:
    # print(e)
    errors.append(str(e))
    return str(e)

#get_vars("{{ all_machine_info | default({}) | combine({ (item | default(default_deployment_item)).vm_name: (item | default(default_deployment_item)).machine_info }, recursive=true) }}")
#get_vars("{{ a | default({}) | combine({ (item | default(b)).vm_name: (item | default(c)).machine_info }, recursive=true) }}")
get_vars("{{ a | default({}) | combine({ (item | default(b)).vm_name: (item | default(c)).machine_info }, recursive=bringme) }}")
# get_vars("{{ a | default(b) }}")
#get_vars("{{ a | default({}) }}")
#  | combine({ (item | default(default_deployment_item)).vm_name: (item | default(default_deployment_item)).machine_info }, recursive=true)
print(all_vars)
print(errors)

# for item in test._entries:
#   print(item)

# print(test)
# pprint(vars(test))
# pprint(vars(test.get_loader()))
