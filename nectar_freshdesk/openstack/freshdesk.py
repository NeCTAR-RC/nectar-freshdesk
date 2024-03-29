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

from freshdesk.v2.api import API as freshdesk_api

from oslo_config import cfg


CONF = cfg.CONF


def get_freshdesk_client():
    domain = CONF.freshdesk.domain
    api_key = CONF.freshdesk.api_key
    return freshdesk_api(domain, api_key)
