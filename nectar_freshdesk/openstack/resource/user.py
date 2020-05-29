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

from oslo_log import log

from prettytable import PrettyTable

from keystoneclient import exceptions as ks_exc

from nectar_freshdesk import config
from nectar_freshdesk.openstack import clients

CONF = config.CONF
LOG = log.getLogger(__name__)


def get_user(username):
    kc = clients.get_keystone_client()
    try:
        user = kc.users.find(name=username)
    except ks_exc.NotFound:
        LOG.debug('User not found: %s', username)
        return None

    info = user._info.copy()

    # Remove stuff
    remove = ['links', 'password_expires_at']
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

    output = '<b>Details for User {}</b>'.format(info.get('id'))
    output += pt.get_html_string(attributes={
        'border': 1,
        'style': 'border-width: 1px; border-collapse: collapse;'
    })
    return output
