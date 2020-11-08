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

import re

import ipaddress

from oslo_log import log


LOG = log.getLogger(__name__)

UUID_REGEX = re.compile(r'[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}', re.I)  # noqa
IPV4_REGEX = re.compile(r'(?:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9]))')  # noqa


def find_uuids(t):
    return list(set(re.findall(UUID_REGEX, t)))


def find_ipv4s(t):
    ipv4_addresses = []
    for ipv4 in set(re.findall(IPV4_REGEX, t)):
        try:
            ip = ipaddress.IPv4Address(ipv4)
            if not ip.is_private:
                ipv4_addresses.append(ipv4)
        except Exception:
            LOG.exception('Unable to parse IPv4 address')

    return ipv4_addresses
