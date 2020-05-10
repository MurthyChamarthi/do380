import json
import re

def is_connection_opt(s):
    m = re.match(r'--([a-z-]+)(=|$)', s)
    return m and m.group(1) in (
        'as',
        'as-group',
	'certificate-authority',
        'client-certificate',
        'client-key',
        'cluster',
        'config',
        'context',
        'insecure-skip-tls-verify',
        'kubeconfig',
        'match-server-version',
        'request-timeout',
        'server',
        'token',
        'user'
    )

def format_change_command(value):
    cmd = [
        str(item) for item in value['cmd']
        if not is_connection_opt(item)
    ]
    if cmd[0] == 'echo':
        cmd.pop(0)
    return {
        'action': 'command',
        'command': cmd
    }

def format_change_provision(value):
    kind = value['resource']['kind']
    change = {
        'action': str(value['action']),
        'kind': str(kind),
        'name': str(value['resource']['metadata']['name'])
    }
    if 'namespace' in value['resource']['metadata']:
        change['namespace'] = str(value['resource']['metadata']['namespace'])
    if kind != 'Secret':
        if value.get('patch', None):
            change['patch'] = value['patch']
        else:
            change['resource'] = value['resource']
    return change

def record_change(change, change_record):
    fh = open(change_record, 'a')
    fh.write("---\n")
    for k in sorted(change):
        v = change[k]
        if isinstance(v, str):
            fh.write("{}: {}\n".format(k, v))
        elif k == 'command':
            fh.write("command: {}\n".format(
                 ' '.join(v)
            ))
        else:
            fh.write("{}: |\n  {}\n".format(
                k,
                json.dumps(
                    v,
                    indent=2,
                    separators=(',',': ')
                ).replace("\n", "\n  ")
            ))

def record_change_command(value, change_record=''):
    if change_record:
        record_change(
            format_change_command(value),
            change_record
        )
    return True

def record_change_provision(value, change_record=''):
    if value['changed'] and change_record:
        record_change(
            format_change_provision(value),
            change_record
        )
    return value['changed']

class FilterModule(object):
    '''
    custom jinja2 filters for working with collections
    '''

    def filters(self):
        return {
            'record_change_command': record_change_command,
            'record_change_provision': record_change_provision
        }
