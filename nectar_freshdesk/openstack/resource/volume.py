#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json

from cinderclient import exceptions as cinder_exc

from oslo_config import cfg
from oslo_log import log

from prettytable import PrettyTable

from nectar_freshdesk.openstack import clients


CONF = cfg.CONF
LOG = log.getLogger(__name__)


def get_volume(volume_id):
    cc = clients.get_cinder_client()

    try:
        volume = cc.volumes.get(volume_id)
    except cinder_exc.NotFound:
        LOG.debug("Volume %s not found", volume_id)
        return None

    info = volume._info.copy()

    # Project
    project_id = info.pop('os-vol-tenant-attr:tenant_id')
    if project_id:
        try:
            project = clients.get_project(project_id)
            info['project_id'] = f'{project.name} ({project.id})'
            # populate volume project table detail
        except Exception:
            info['project_id'] = f'Project not found ({project_id})'

    # User
    user_id = info.get('user_id')
    if user_id:
        try:
            user = clients.get_user(user_id)
            info['user_id'] = f'{user.name} ({user.id})'
        except Exception:
            pass

    # Remove stuff
    remove = ['links', 'addresses', 'hostId']
    for item in remove:
        info.pop(item, None)

    pt = PrettyTable(['Property', 'Value'], caching=False)
    pt.align = 'l'
    for k, v in sorted(info.items()):
        if isinstance(v, (dict, list)):
            v = json.dumps(v)
        # if value has a newline, add in multiple rows
        # e.g. fault with stacktrace
        if v and isinstance(v, str) and (r'\n' in v or '\r' in v):
            v = v.replace('\r', '')  # \r' would break the table, so remove
            lines = v.strip().split(r'\n')
            col1 = k
            for line in lines:
                pt.add_row([col1, line])
                col1 = ''
        else:
            if v is None:
                v = '-'
            pt.add_row([k, v])

    output = '<b>Details for Volume {}</b>'.format(info.get('id'))
    output += pt.get_html_string(
        attributes={
            'border': 1,
            'style': 'border-width: 1px; border-collapse: collapse;',
        }
    )
    if project:
        p = project._info
        tt = PrettyTable(['Property', 'Value'], caching=False)
        tt.align = 'l'
        remove = ['parent_id', 'is_domain', 'tags', 'links']
        [tt.add_row([k, v]) for k, v in p.items() if k not in remove]
        output += '<br><b>Project for Instance {}</b>'.format(info.get('id'))
        output += tt.get_html_string(
            attributes={
                'border': 1,
                'style': 'border-width: 1px; border-collapse: collapse;',
            }
        )
    return output
