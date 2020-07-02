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

from novaclient import exceptions as nova_exc
from prettytable import PrettyTable

from oslo_log import log

from nectar_freshdesk import config
from nectar_freshdesk.openstack import clients


CONF = config.CONF
LOG = log.getLogger(__name__)


def get_instance(instance_id):
    gc = clients.get_glance_client()
    nc = clients.get_nova_client()

    try:
        instance = nc.servers.get(instance_id)
    except nova_exc.NotFound:
        LOG.debug("Instance {} not found".format(instance_id))
        return None

    info = instance._info.copy()

    # Networks
    for network_label, address_list in instance.networks.items():
        info['%s network' % network_label] = ', '.join(address_list)

    # Flavor
    flavor_id = getattr(instance, 'flavor', {}).get('id')
    if flavor_id:
        try:
            flavor = nc.flavors.get(flavor_id)
            info['flavor'] = '%s (%s)' % (flavor.name, flavor_id)
        except Exception:
            info['flavor'] = '%s (%s)' % ("Flavor not found", flavor_id)

    # Image
    image = info.get('image', {})
    if image:
        image_id = image.get('id', '')
        try:
            img = gc.images.get(image_id)
            nectar_build = img.get('nectar_build', 'N/A')
            info['image'] = ('%s (%s, Nectar Build %s)'
                             % (img.name, img.id, nectar_build))
        except Exception:
            info['image'] = 'Image not found (%s)' % image_id

    else:  # Booted from volume
        info['image'] = "Attempt to boot from volume - no image supplied"

    # Project
    project_id = info.pop('tenant_id')
    if project_id:
        try:
            project = clients.get_project(project_id)
            info['project_id'] = '%s (%s)' % (project.name, project.id)
            # populate instance project table detail
        except Exception:
            info['project_id'] = 'Project not found (%s)' % project_id

    # User
    user_id = info.get('user_id')
    if user_id:
        try:
            user = clients.get_user(user_id)
            info['user_id'] = '%s (%s)' % (user.name, user.id)
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

    # Get instance actions
    actions = nc.instance_action.list(instance_id)
    at = PrettyTable(['action', 'date', 'user', 'project'])
    at.align = 'l'
    for a in actions:
        user = clients.get_user(a.user_id)
        project = clients.get_project(a.project_id)
        at.add_row([a.action, a.start_time, user.name, project.name])

    output = '<b>Details for Instance {}</b>'.format(info.get('id'))
    output += pt.get_html_string(attributes={
        'border': 1,
        'style': 'border-width: 1px; border-collapse: collapse;'
    })
    if project:
        p = project._info
        tt = PrettyTable(['Property', 'Value'], caching=False)
        tt.align = 'l'
        for k, v in p.items():
            tt.add_row([k, v])
        output += '<b>Project for Instance {}</b>'.format(info.get('id'))
        output += tt.get_html_string(attributes={
            'border': 1,
            'style': 'border-width: 1px; border-collapse: collapse;'
           })
    output += '<br><b>Actions for Instance {}</b>'.format(info.get('id'))
    output += at.get_html_string(attributes={
        'border': 1,
        'style': 'border-width: 1px; border-collapse: collapse;'
    })
    return output
