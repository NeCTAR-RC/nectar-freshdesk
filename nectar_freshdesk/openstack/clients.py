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

from cinderclient import client as cinder_client
from glanceclient import client as glance_client

from keystoneauth1 import exceptions as ks_exc
from keystoneauth1 import loading as ks_loading
from keystoneauth1 import session as ks_session
from keystoneclient.v3 import client as ks_client_v3
from neutronclient.neutron import client as neutron_client
from novaclient import client as nova_client
from novaclient import exceptions as nova_exc

from oslo_config import cfg
from oslo_log import log


CONF = cfg.CONF
LOG = log.getLogger(__name__)

_SESSION = None
_AUTH = None


def get_session():
    """Get a service credentials auth session."""
    global _SESSION  # pylint: disable=global-statement
    global _AUTH  # pylint: disable=global-statement

    if not _AUTH:
        _AUTH = ks_loading.load_auth_from_conf_options(CONF, 'service_auth')
    if not _SESSION:
        _SESSION = ks_session.Session(auth=_AUTH)
    return _SESSION


def get_keystone_client():
    session = get_session()
    return ks_client_v3.Client(session=session)


def get_nova_client(version='2.87'):
    session = get_session()
    return nova_client.Client(version, session=session)


def get_neutron_client(version='2.0'):
    session = get_session()
    return neutron_client.Client(version, session=session)


def get_glance_client(version='2'):
    session = get_session()
    return glance_client.Client(version, session=session)


def get_cinder_client(version='3'):
    session = get_session()
    return cinder_client.Client(version, session=session)


def get_project(project_id):
    """Add access to project_cache to store all project objects"""
    k = get_keystone_client()
    project = None
    try:
        project = k.projects.get(project_id)
    except ks_exc.NotFound:
        LOG.debug('Project not found: %s', project_id)
    return project


def get_user(user_id):
    """Get a user from an id"""
    k = get_keystone_client()
    user = None
    try:
        user = k.users.get(user_id)
    except ks_exc.NotFound:
        LOG.debug('User not found: %s', user_id)
    return user


def get_roles(user):
    k = get_keystone_client()
    roles = k.role_assignments.list(user=user, include_names=True)
    return roles


def get_instance(instance_id):
    n = get_nova_client()
    instance = None
    try:
        instance = n.servers.get(instance_id)
    except nova_exc.NotFound:
        LOG.debug('Instance not found: %s', instance_id)
    return instance


def list_instances(**kwargs):
    n = get_nova_client()
    search_opts = {'all_tenants': True}
    search_opts.update(kwargs)
    return n.servers.list(search_opts=search_opts)
