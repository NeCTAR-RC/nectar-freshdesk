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

import sys

from keystoneauth1 import loading as ks_loading

from oslo_config import cfg
from oslo_log import log

LOG = log.getLogger(__name__)


CONF = cfg.CONF

# Tag on ticket to indicate if it's been processed
PROCESSED_TAG = 'bot-processed'

# Fields required in JSON message
REQUIRED_FIELDS = ('action', 'ticket_id', 'source', 'email')

_DEFAULT_LOG_LEVELS = ['amqp=WARN', 'amqplib=WARN',
                       'requests.packages.urllib3.connectionpool=WARN',
                       'urllib3.connectionpool=WARN', 'websocket=WARN',
                       'keystonemiddleware=WARN']

auth_opts = [
    cfg.StrOpt('service_url',
               required=True,
               help='URL as given in the AAF Service Registration'),
    cfg.StrOpt('aaf_login_url',
               required=True,
               help='AAF RapidConnect login URL'),
    cfg.StrOpt('aaf_secret',
               required=True,
               secret=True,
               help='AAF RapidConnect secret'),
]

freshdesk_opts = [
    cfg.StrOpt('sso_url',
               required=True,
               help='Freshdesk SSO URL'),
    cfg.StrOpt('sso_key',
               required=True,
               secret=True,
               help='Freshdesk SSO key'),
    cfg.StrOpt('domain',
               default='dhdnectar.freshdesk.com',
               help='FreshDesk domain to use'),
    cfg.StrOpt('api_key',
               required=True,
               help='FreshDesk API key'),
]

flask_opts = [
    cfg.StrOpt('secret_key',
               secret=True),
]

cfg.CONF.register_opts(freshdesk_opts, group='freshdesk')
cfg.CONF.register_opts(flask_opts, group='flask')
cfg.CONF.register_opts(auth_opts, group='auth')

log.register_options(cfg.CONF)

ks_loading.register_auth_conf_options(cfg.CONF, 'keystone_authtoken')


def init(args=[], conf_file='/etc/nectar-freshdesk/nectar-freshdesk.conf'):
    cfg.CONF(
        args,
        project='nectar-freshdesk',
        default_config_files=[conf_file])


def setup_logging(conf):
    """Sets up the logging options for a log with supplied name.

    :param conf: a cfg.ConfOpts object
    """
    product_name = 'nectar-freshdesk'

    log.setup(conf, product_name)
    LOG.info("Logging enabled!")
    LOG.debug("command line: %s", " ".join(sys.argv))
