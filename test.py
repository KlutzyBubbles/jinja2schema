#!/usr/bin/python

from pprint import pprint
import jinja2
from jinja2 import Environment, PackageLoader, meta
import ansible.plugins.filter.core
import ansible.plugins.filter.mathstuff
import ansible.plugins.filter.urls
import ansible.plugins.filter.urlsplit
import jinja2schema

loader = DataLoader()
loader.set_basedir('.')

filters = [
  ansible.plugins.filter.core.FilterModule(),
  ansible.plugins.filter.mathstuff.FilterModule(),
  ansible.plugins.filter.urls.FilterModule(),
  ansible.plugins.filter.urlsplit.FilterModule()
]
config = jinja2schema.Config(CUSTOM_FILTERS=filters)

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
    return list(variables)
  except Exception, e:
    errors.append(str(e))
    return str(e)

print(get_vars("{{ (gpg_key_directory_permission.stat.mode <= '0755') and (( gpg_fingerprints.stdout_lines | difference(gpg_valid_fingerprints)) | length == 0) and (gpg_fingerprints.stdout_lines | length > 0) and (ansible_distribution == \"RedHat\") }}"))

print(all_vars)

# for item in test._entries:
#   print(item)

# print(test)
# pprint(vars(test))
# pprint(vars(test.get_loader()))
