from .access_type import AccessType
import pprint

MAGIC_VARS = {
  "ansible_check_mode": True,
  "ansible_config_file": True,
  "ansible_dependent_role_names": True,
  "ansible_diff_mode": True,
  "ansible_forks": True,
  "ansible_inventory_sources": True,
  "ansible_limit": True,
  "ansible_loop": True,
  "ansible_loop_var": True,
  "ansible_index_var": True,
  "ansible_parent_role_names": True,
  "ansible_parent_role_paths": True,
  "ansible_play_batch": True,
  "ansible_play_hosts": True,
  "ansible_play_hosts_all": True,
  "ansible_play_role_names": True,
  "ansible_playbook_python": True,
  "ansible_role_names": True,
  "ansible_role_name": True,
  "ansible_collection_name": True,
  "ansible_run_tags": True,
  "ansible_search_path": True,
  "ansible_skip_tags": True,
  "ansible_verbosity": True,
  "ansible_version": True,
  "group_names": True,
  "groups": True,
  "inventory_hostname": True,
  "inventory_hostname_short": True,
  "inventory_dir": True,
  "inventory_file": True,
  "play_hosts": True,
  "ansible_play_name": True,
  "playbook_dir": True,
  "role_name": True,
  "role_names": True,
  "role_path": True,
  "ansible_local": True,
  "ansible_become_user": True,
  "ansible_connection": True,
  "ansible_host": True,
  "ansible_python_interpreter": True,
  "ansible_user": True,
  "hostvars": True,
  "omit": True,
  "ansible_facts": {
    "ansible_all_ipv4_addresses": True,
    "ansible_all_ipv6_addresses": True,
    "ansible_apparmor": {
        "status": True
    },
    "ansible_architecture": True,
    "ansible_bios_date": True,
    "ansible_bios_version": True,
    "ansible_cmdline": True,
    "ansible_date_time": {
        "date": True,
        "day": True,
        "epoch": True,
        "hour": True,
        "iso8601": True,
        "iso8601_basic": True,
        "iso8601_basic_short": True,
        "iso8601_micro": True,
        "minute": True,
        "month": True,
        "second": True,
        "time": True,
        "tz": True,
        "tz_offset": True,
        "weekday": True,
        "weekday_number": True,
        "weeknumber": True,
        "year": True
    },
    "ansible_default_ipv4": {
        "address": True,
        "alias": True,
        "broadcast": True,
        "gateway": True,
        "interface": True,
        "macaddress": True,
        "mtu": True,
        "netmask": True,
        "network": True,
        "type": True
    },
    "ansible_default_ipv6": True,
    "ansible_device_links": {
        "ids": True,
        "labels": True,
        "masters": True,
        "uuids": True
    },
    "ansible_devices": True,
    "ansible_distribution": True,
    "ansible_distribution_file_parsed": True,
    "ansible_distribution_file_path": True,
    "ansible_distribution_file_variety": True,
    "ansible_distribution_major_version": True,
    "ansible_distribution_release": True,
    "ansible_distribution_version": True,
    "ansible_dns": {
        "nameservers": True
    },
    "ansible_domain": True,
    "ansible_effective_group_id": True,
    "ansible_effective_user_id": True,
    "ansible_env": {
        "HOME": True,
        "LANG": True,
        "LESSOPEN": True,
        "LOGNAME": True,
        "MAIL": True,
        "PATH": True,
        "PWD": True,
        "SELINUX_LEVEL_REQUESTED": True,
        "SELINUX_ROLE_REQUESTED": True,
        "SELINUX_USE_CURRENT_RANGE": True,
        "SHELL": True,
        "SHLVL": True,
        "SSH_CLIENT": True,
        "SSH_CONNECTION": True,
        "USER": True,
        "XDG_RUNTIME_DIR": True,
        "XDG_SESSION_ID": True,
        "_": True
    },
    "ansible_eth0": {
        "active": True,
        "device": True,
        "ipv4": {
            "address": True,
            "broadcast": True,
            "netmask": True,
            "network": True
        },
        "ipv6": True,
        "macaddress": True,
        "module": True,
        "mtu": True,
        "pciid": True,
        "promisc": True,
        "type": True
    },
    "ansible_eth1": {
        "active": True,
        "device": True,
        "ipv4": {
            "address": True,
            "broadcast": True,
            "netmask": True,
            "network": True
        },
        "ipv6": True,
        "macaddress": True,
        "module": True,
        "mtu": True,
        "pciid": True,
        "promisc": True,
        "type": True
    },
    "ansible_fips": True,
    "ansible_form_factor": True,
    "ansible_fqdn": True,
    "ansible_hostname": True,
    "ansible_interfaces": True,
    "ansible_is_chroot": True,
    "ansible_kernel": True,
    "ansible_lo": {
        "active": True,
        "device": True,
        "ipv4": {
            "address": True,
            "broadcast": True,
            "netmask": True,
            "network": True
        },
        "ipv6": True,
        "mtu": True,
        "promisc": True,
        "type": True
    },
    "ansible_local": True,
    "ansible_lsb": {
        "codename": True,
        "description": True,
        "id": True,
        "major_release": True,
        "release": True
    },
    "ansible_machine": True,
    "ansible_machine_id": True,
    "ansible_memfree_mb": True,
    "ansible_memory_mb": {
        "nocache": {
            "free": True,
            "used": True
        },
        "real": {
            "free": True,
            "total": True,
            "used": True
        },
        "swap": {
            "cached": True,
            "free": True,
            "total": True,
            "used": True
        }
    },
    "ansible_memtotal_mb": True,
    "ansible_mounts": True,
    "ansible_nodename": True,
    "ansible_os_family": True,
    "ansible_pkg_mgr": True,
    "ansible_processor": True,
    "ansible_processor_cores": True,
    "ansible_processor_count": True,
    "ansible_processor_nproc": True,
    "ansible_processor_threads_per_core": True,
    "ansible_processor_vcpus": True,
    "ansible_product_name": True,
    "ansible_product_serial": True,
    "ansible_product_uuid": True,
    "ansible_product_version": True,
    "ansible_python": {
        "executable": True,
        "has_sslcontext": True,
        "type": True,
        "version": {
            "major": True,
            "micro": True,
            "minor": True,
            "releaselevel": True,
            "serial": True
        },
        "version_info": True
    },
    "ansible_python_version": True,
    "ansible_real_group_id": True,
    "ansible_real_user_id": True,
    "ansible_selinux": {
        "config_mode": True,
        "mode": True,
        "policyvers": True,
        "status": True,
        "type": True
    },
    "ansible_selinux_python_present": True,
    "ansible_service_mgr": True,
    "ansible_ssh_host_key_ecdsa_public": True,
    "ansible_ssh_host_key_ed25519_public": True,
    "ansible_ssh_host_key_rsa_public": True,
    "ansible_swapfree_mb": True,
    "ansible_swaptotal_mb": True,
    "ansible_system": True,
    "ansible_system_capabilities": True,
    "ansible_system_capabilities_enforced": True,
    "ansible_system_vendor": True,
    "ansible_uptime_seconds": True,
    "ansible_user_dir": True,
    "ansible_user_gecos": True,
    "ansible_user_gid": True,
    "ansible_user_id": True,
    "ansible_user_shell": True,
    "ansible_user_uid": True,
    "ansible_userspace_architecture": True,
    "ansible_userspace_bits": True,
    "ansible_virtualization_role": True,
    "ansible_virtualization_type": True,
    "gather_subset": True,
    "module_setup": True
  }
}

class Scope(object):

  def __init__(self, parent=None, host=None, magic_vars=MAGIC_VARS):
    self.parent = parent
    self.host = host
    self.children = []
    self.variables = {}
    if self.parent is None:
      self.inject_magic_vars(magic_vars=MAGIC_VARS)

  def inject_magic_vars(self, magic_vars=MAGIC_VARS, trail=[]):
    for key, value in magic_vars.items():
      if isinstance(value, dict):
        temp = list(trail)
        temp.append(key)
        self.inject_magic_vars(value, temp)
      else:
        if len(trail) == 0:
          self.add_variable(key, 'magic')
        else:
          temp = list(trail)
          temp.append(key)
          self.add_attribute(temp.pop(0), temp, 'magic')

  def __repr__(self):
    return pprint.pformat(self.variables)

  def add_variable(self, name, action, ignore_parent=False):
    if ignore_parent or self.parent is None:
      if name not in self.variables:
        self.variables[name] = AccessType()
      self.variables[name].add(action)
    elif not self.parent.add_variable(name, action, ignore_parent=ignore_parent):
      return self.add_variable(name, action, ignore_parent=True)
    return True

  def add_attribute(self, name, attribute, action, ignore_parent=False):
    if ignore_parent or self.parent is None:
      if name not in self.variables:
        self.variables[name] = AccessType()
      self.variables[name].add(action)
      self.variables[name].add_attribute(attribute, action)
    elif not self.parent.add_attribute(name, attribute, action, ignore_parent=ignore_parent):
      return self.add_attribute(name, attribute, action, ignore_parent=True)
    return True

  def construct_with_attr(self, name, with_history=False):
    if name not in self.variables:
      return {}
    return self.variables[name].construct_from_attr(with_history=with_history)

  def is_undefined(self, name, trail=[]):
    print ('--is_undefined')
    if name == 'undefined':
      if name not in self.variables:
        print('Not in variables')
        return True
      if self.variables[name].is_undefined():
        print('is undefined')
        if self.parent is not None:
          print('parent not none')
          return self.parent.is_undefined(name, trail)
        return True
      return False
    if len(trail) > 0:
      print (name)
      current_vars = self.variables
      for key in trail:
        if key not in current_vars:
          return True
        current_vars = current_vars[key]
      if name not in current_vars:
        return True
      if current_vars[name].is_undefined():
        if self.parent is not None:
          return self.parent.is_undefined(name, trail)
        return True
    else:
      if name not in self.variables:
        return True
      if self.variables[name].is_undefined():
        if self.parent is not None:
          return self.parent.is_undefined(name, trail)
        return True
    return False

  def is_magic(self, name):
    if name not in self.variables:
      return False
    if self.variables[name].is_magic():
      if self.parent is not None:
        return self.parent.is_magic(name)
      return True
    return False

  def is_magic_used(self, name):
    if name not in self.variables:
      return False
    if self.variables[name].is_magic_used():
      if self.parent is not None:
        return self.parent.is_magic_used(name)
      return True
    return False

  def get_undefined(self, trail=[], exclude_magic=True, with_history=False):
    output = {}
    mod_trail = list(trail)
    if len(mod_trail) > 0:
      trail_popped = mod_trail.pop(0)
      variable = self.variables[trail_popped]
      if len(mod_trail) > 0:
        for trail_key in mod_trail:
          if trail_key in variable.attributes.keys():
            trail_popped = trail_key
            variable = variable.attributes[trail_key]
          else:
            return output
      if variable.has_attr():
        for key in variable.attributes.keys():
          if variable.attributes[key].has_attr():
            temp = list(trail)
            temp.append(key)
            child_undefined = self.get_undefined(trail=temp, exclude_magic=True, with_history=with_history)
            if len(child_undefined.keys()) != 0:
              if key not in output.keys():
                output[key] = {}
              output[key] = child_undefined
          else:
            if variable.attributes[key].is_undefined():
              output[key] = variable.attributes[key].construct_from_attr(with_history=with_history)
      else:
        if variable.is_undefined():
          output[trail_popped] = variable.construct_from_attr(with_history=with_history)
    else:
      for key in self.variables.keys():
        if exclude_magic and self.is_magic(key):
          continue
        if self.variables[key].has_attr():
          temp = list(trail)
          temp.append(key)
          child_undefined = self.get_undefined(trail=temp, exclude_magic=True, with_history=with_history)
          if len(child_undefined.keys()) != 0:
            if key not in output.keys():
              output[key] = {}
            output[key] = child_undefined
        else:
          if self.is_undefined(key):
            output[key] = self.construct_with_attr(key, with_history=with_history)
    return output

  def get_all(self, exclude_magic=True, with_history=True):
    output = {}
    for key in self.variables.keys():
      if exclude_magic and self.is_magic(key):
        if not self.is_magic_used(key):
          continue
      output[key] = self.construct_with_attr(key, with_history=with_history)
    return output

  def get_debug(self, exclude_magic=True):
    output = {}
    for key in self.variables.keys():
      if exclude_magic and self.is_magic(key):
        continue
      output[key] = self.construct_with_history(key)
    return output

  def create_child(self):
    self.children.append(Scope(parent=self))
    return self.children[-1]

  def has_attributes(self):
    return len(self.variables.keys()) > 0
