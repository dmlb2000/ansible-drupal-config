#!/usr/bin/python3

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'status': ['preview'],
    'supported_by': 'Pacifica'
}

DOCUMENTATION = '''
---
module: drupal_config

short_description: This module defines drupal 8+ configurations

version_added: "2.4"

description:
    - "This is my longer description explaining my test module"

options:
    id:
        description:
            - The full ID string of the configuration in Drupal.
        required: true
    config:
        description:
            - The configuration document (in yaml) to define in Drupal.
        required: true
    merge:
        description:
            - Merge the existing configuration with the one defined.
        required: false
    root:
        description:
            - The Drupal project root.
        required: false
    drush_path:
        description:
            - The full path to the drush command
        require: false

author:
    - David Brown (@dmlb2000)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_test:
    id: system.theme
    config:
      default: bartik
'''

RETURN = '''
old_config:
    description: The previous configuration document.
    type: dict
    returned: always
config:
    description: The new generated configuration document.
    type: dict
    returned: always
'''
from io import StringIO
from subprocess import Popen, PIPE
try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory
import os, sys
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper
from jinja2 import Template
from ansible.module_utils.basic import AnsibleModule

class DrushException(Exception):
    pass

def _call(args, stdout, stderr):
    with open()

def _drupal_strip_config(yaml_data):
    for key in ['_core']:
        del yaml_data[key]
    return yaml_data

def _drush_set(drush_path, root, config_id, config_data):
    stdout_buf = StringIO()
    stderr_buf = StringIO()
    with TemporaryDirectory() as temp_dir:
        with open(os.path.join(temp_dir, '{}.yml'.format(config_id)), 'w') as config_fd:
            config_fd.write(dump(config_data, Dumper=Dumper))
        if call([drush_path, '--yes', '--root', root, 'config:import', '--partial', '--source', temp_dir], stdout=stdout_buf, stderr=stderr_buf) != 0:
            stderr_buf.seek(0)
            raise DrushException('Config import failed {}'.format(stderr_buf.read()))
    

def _drush_get(drush_path, root, config_id):
    stdout_buf = StringIO()
    stderr_buf = StringIO()
    if call([drush_path, '--yes', '--root', root, 'config:get', config_id], stdout=stdout_buf, stderr=stderr_buf) != 0:
        stderr_buf.seek(0)
        if 'Config {} does not exist'.format(config_id) in stderr_buf.read():
            return None
        stderr_buf.seek(0)
        raise DrushException('Some other Drush exception happened {}'.format(stderr_buf.read()))
    stdout_buf.seek(0)
    yaml_data = load(stdout_buf.read(), Loader=Loader)
    stdout_buf.seek(0)
    clean_data = _drupal_strip_config(load(stdout_buf.read(), Loader=Loader))
    return yaml_data, clean_data

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        id=dict(type='str', required=True),
        config=dict(type='dict', required=True),
        merge=dict(type='bool', required=False, default=True),
        root=dict(type='str', required=False, default=os.getcwd()),
        drush_path=dict(type='str', required=False, default='drush')
    )

    result = dict(
        changed=False,
        old_config='',
        config=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    try:
        yaml_data, clean_data = _drush_get(module.params['drush_path'], module.params['root'], module.params['id'])
    except DrushException:
        module.fail_json(msg='{0}\n{1}\n{2}\n'.format(*sys.exc_info()), **result)
    result['old_config'] = yaml_data

    if module.check_mode:
        module.exit_json(**result)

    if module.params['merge']:
        t = Template("{{ old_config | combine(config, recursive=True) }}!")
        new_data = load(t.render(old_config=clean_data, config=module.params['config']), Loader=Loader)
    else:
        new_data = module.params['config']

    dump_args = {
        'default_flow_style': False
    }
    new_str = dump(new_data, **dump_args)
    old_str = dump(clean_data, **dump_args)
    if new_str == old_str:
        result['config'] = new_data
        module.exit_json(**result)

    result['changed'] = True
    try:
        _drush_set(module.params['drush_path'], module.params['root'], module.params['id'], new_data)
    except DrushException:
        module.fail_json(msg='{0}\n{1}\n{2}\n'.format(*sys.exc_info()), **result)
    
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()