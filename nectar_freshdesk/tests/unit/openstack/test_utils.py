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

from nectar_freshdesk.openstack import utils
from nectar_freshdesk.tests.unit import base


class TestOpenStackUtils(base.TestCase):

    def test_find_uuids(self):
        test_string = ("this is a f9a310d6-5734-4e5d-9e76-2c5142fcee8e \n"
                       "found in a string")
        expected = ['f9a310d6-5734-4e5d-9e76-2c5142fcee8e']
        result = utils.find_uuids(test_string)
        self.assertCountEqual(result, expected)

    def test_find_ipv4s(self):
        test_string = ("this is 2.2.2.2 an \n"
                       "1.1.1.1 ip address")
        expected = ['1.1.1.1', '2.2.2.2']
        result = utils.find_ipv4s(test_string)
        self.assertCountEqual(result, expected)

    def test_find_ipv4s_ignore_private(self):
        test_string = ("this is a 10.0.0.1 private address")
        expected = []
        result = utils.find_ipv4s(test_string)
        self.assertCountEqual(result, expected)
