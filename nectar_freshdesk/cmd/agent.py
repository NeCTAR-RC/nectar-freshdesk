#!/usr/bin/env python
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

from oslo_config import cfg
from oslo_log import log

from nectar_freshdesk import config
from nectar_freshdesk.openstack import agent


CONF = cfg.CONF
LOG = log.getLogger(__name__)


class main:
    config.init(sys.argv[1:])
    config.setup_logging(CONF)
    LOG.info('Starting agent')
    a = agent.Agent()
    a.run()


if __name__ == '__main__':
    main()
