from access_type import AccessType
import pprint

MAGIC_VARS = {
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

class Scope(object):

  def __init__(self, parent=None, host=None):
    self.parent = parent
    self.host = host
    self.children = []
    self.variables = {}
    if self.parent is None:
      self.inject_magic_vars()

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

  def is_undefined(self, name):
    if name not in self.variables:
      return True
    if self.variables[name].is_undefined():
      if self.parent is not None:
        return self.parent.is_undefined(name)
      return True
    return False

  def is_magic(self, name):
    if name not in self.variables:
      return True
    if self.variables[name].is_magic():
      if self.parent is not None:
        return self.parent.is_magic(name)
      return True
    return False

  def get_undefined(self, exclude_magic=True, with_history=False):
    output = {}
    for key in self.variables.keys():
      if exclude_magic and self.is_magic(key):
        continue
      if self.is_undefined(key):
        output[key] = self.construct_with_attr(key, with_history=with_history)
    return output

  def get_all(self, exclude_magic=True):
    output = {}
    for key in self.variables.keys():
      if exclude_magic and self.is_magic(key):
        continue
      output[key] = self.construct_with_attr(key, with_history=True)
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
