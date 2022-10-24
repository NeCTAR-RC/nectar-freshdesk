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

from oslo_config import cfg

import oslo_messaging


CONF = cfg.CONF


def get_target():
    oslo_messaging.set_transport_defaults('nectar-freshdesk')
    return oslo_messaging.Target(exchange='nectar-freshdesk',
                                 topic='nectar-freshdesk',
                                 server='info',
                                 version='1.0')


def get_rpc_server(endpoint):
    """Return a configured oslo_messaging rpc server."""
    transport = oslo_messaging.get_rpc_transport(CONF)
    target = get_target()
    return oslo_messaging.get_rpc_server(transport, target, [endpoint],
                                         executor='threading')


def get_rpc_client():
    """Return a configured oslo_messaging RPCClient."""
    transport = oslo_messaging.get_rpc_transport(CONF)
    target = get_target()
    return oslo_messaging.RPCClient(transport, target)
