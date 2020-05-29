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

from oslo_log import log

from prettytable import PrettyTable

from keystoneclient import exceptions as ks_exc

from nectar_freshdesk import config
from nectar_freshdesk.openstack import clients

CONF = config.CONF
LOG = log.getLogger(__name__)


def get_roles(username):
    kc = clients.get_keystone_client()
    try:
        user = kc.users.find(name=username)
    except ks_exc.NotFound:
        LOG.debug('User not found: %s', username)
        return None

    roles = kc.role_assignments.list(user=user, include_names=True)

    pt = PrettyTable(['Role', 'Project'], caching=False)
    for r in roles:
        pt.add_row([r.role.get('name'),
                    '%s (%s)' % (r.scope['project'].get('id'),
                                 r.scope['project'].get('name'))])
    output = '<b>Role Details</b>'
    output += pt.get_html_string(attributes={
        'border': 1,
        'style': 'border-width: 1px; border-collapse: collapse;'
    })
    return output
