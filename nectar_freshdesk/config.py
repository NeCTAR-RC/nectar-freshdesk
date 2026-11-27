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

import copy
import operator

from keystoneauth1 import loading as ks_loading
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging

LOG = logging.getLogger(__name__)

PROJECT_NAME = 'nectar-freshdesk'

# Tag on ticket to indicate if it's been processed
PROCESSED_TAG = 'bot-processed'

# Tag on ticket to indicate the AI triage note has been added
TRIAGE_TAG = 'ai-triaged'

# Fields required in JSON message
REQUIRED_FIELDS = ('action', 'ticket_id', 'source', 'email')

_DEFAULT_LOG_LEVELS = [
    'amqp=WARN',
    'amqplib=WARN',
    'requests.packages.urllib3.connectionpool=WARN',
    'urllib3.connectionpool=WARN',
    'websocket=WARN',
    'keystonemiddleware=WARN',
]

freshdesk_opts = [
    cfg.StrOpt(
        'domain',
        default='dhdnectar.freshdesk.com',
        help='FreshDesk domain to use',
    ),
    cfg.StrOpt(
        'api_key', required=True, secret=True, help='FreshDesk API key'
    ),
]

flask_opts = [
    cfg.StrOpt('secret_key', help="Flask secret key", secret=True),
    cfg.StrOpt(
        'host', help="The host or IP address to bind to", default='0.0.0.0'
    ),
    cfg.IntOpt('port', help="The port to listen on", default=8613),
]

triage_opts = [
    cfg.BoolOpt(
        'enabled',
        default=False,
        help='Ask the AI triage agent to investigate tickets',
    ),
    cfg.StrOpt(
        'agent_url',
        help='A2A JSON-RPC URL of the triage agent, for example '
        'https://agents.example.com/agents/<namespace>/<agent>',
    ),
    cfg.StrOpt(
        'token_url',
        help='Keycloak token endpoint used to get a client credentials '
        'token for the agent',
    ),
    cfg.StrOpt('client_id', help='Keycloak client ID'),
    cfg.StrOpt('client_secret', secret=True, help='Keycloak client secret'),
    cfg.StrOpt('scope', help='Optional scope to request with the token'),
    cfg.ListOpt(
        'actions',
        default=['create'],
        help='Webhook actions that trigger a triage',
    ),
    cfg.IntOpt(
        'timeout',
        default=900,
        help='Seconds to wait for the agent to finish a triage',
    ),
    cfg.IntOpt(
        'poll_interval',
        default=10,
        help='Seconds between checks of a running triage',
    ),
    cfg.IntOpt(
        'http_timeout',
        default=30,
        help='Timeout in seconds of each HTTP request to the agent',
    ),
    cfg.IntOpt(
        'retries',
        default=3,
        help='Attempts made when the agent cannot be reached',
    ),
]

cfg.CONF.register_opts(freshdesk_opts, group='freshdesk')
cfg.CONF.register_opts(triage_opts, group='triage')
cfg.CONF.register_opts(flask_opts, group='flask')

logging.register_options(cfg.CONF)

oslo_messaging.set_transport_defaults(control_exchange='nectar-freshdesk')

ks_loading.register_auth_conf_options(cfg.CONF, 'service_auth')


def init(args=None, conf_file=None):
    conf_files = None
    if conf_file:
        conf_files = [conf_file]
    cfg.CONF(args or [], project=PROJECT_NAME, default_config_files=conf_files)


def setup_logging(conf):
    """Sets up the logging options for a log with supplied name.

    :param conf: a cfg.ConfOpts object
    """
    logging.setup(conf, PROJECT_NAME)
    LOG.info("Logging enabled!")


def add_auth_opts():
    opts = ks_loading.register_session_conf_options(cfg.CONF, 'service_auth')
    opt_list = copy.deepcopy(opts)
    opt_list.insert(0, ks_loading.get_auth_common_conf_options()[0])
    for plugin_option in ks_loading.get_auth_plugin_conf_options('password'):
        if all(option.name != plugin_option.name for option in opt_list):
            opt_list.append(plugin_option)
    opt_list.sort(key=operator.attrgetter('name'))
    return ('service_auth', opt_list)


# Used by oslo-config-generator entry point
# https://docs.openstack.org/oslo.config/latest/cli/generator.html
def list_opts():
    return [
        ('freshdesk', freshdesk_opts),
        ('flask', flask_opts),
        ('triage', triage_opts),
        add_auth_opts(),
    ]
