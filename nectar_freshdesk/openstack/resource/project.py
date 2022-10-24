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

from oslo_config import cfg
from oslo_log import log

from prettytable import PrettyTable

from keystoneclient import exceptions as ks_exc

from nectar_freshdesk.openstack import clients

CONF = cfg.CONF
LOG = log.getLogger(__name__)


def get_project(project_id):
    kc = clients.get_keystone_client()
    cc = clients.get_nova_client()
    nc = clients.get_neutron_client()
    try:
        project = kc.projects.get(project_id)
    except ks_exc.NotFound:
        LOG.debug('Project not found: %s', project_id)
        return None

    info = project._info.copy()

    # Remove stuff
    remove = ['links']
    for item in remove:
        if item in info:
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

    # get basic quota info
    qt = PrettyTable(['Resource', 'Quota', 'Used'], caching=False)
    qt.align = 'l'
    cq = cc.quotas.get(project_id, detail=True)._info
    del cq['id']
    for res, data in cq.items():
        qt.add_row([res, data['limit'], data['in_use']])
    nq = nc.show_quota_details(project_id)
    remove = ['l7policy', 'member', 'loadbalancer', 'listener',
              'pool', 'healthmonitor']
    for res, data in nq['quota'].items():
        if res not in remove:
            qt.add_row([res, data['limit'], data['used']])

    output = '<b>Details for Project {}</b>'.format(info.get('id'))
    output += pt.get_html_string(attributes={
        'border': 1,
        'style': 'border-width: 1px; border-collapse: collapse;'
    })
    output += '<b>Quota for Project {}</b>'.format(info.get('id'))
    output += qt.get_html_string(attributes={
        'border': 1,
        'style': 'border-width: 1px; border-collapse: collapse;'
    })
    return output
