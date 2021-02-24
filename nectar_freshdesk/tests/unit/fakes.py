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


TICKET_WEBHOOK_INFO = {
    'action': 'create',
    'ticket_id': 1234,
    'email': 'my@user.com',
    'source': 'This is my ticket source',
}

USER_INFO = {
    'id': 'b30642e355494eefad1692dbb508c0c6',
    'name': 'fake@user.com',
    'email': 'fake@user.com',
    'full_name': 'Fake User',
    'enabled': True,
    'domain_id': 'default',
    'default_project_id': 'f6933a0aa39b400dacf65909b38cc3d9',
    'options': {},
}

PROJECT_INFO = {
    'id': 'f6933a0aa39b400dacf65909b38cc3d9',
    'name': 'Fake Project',
    'description': 'This is a fake project',
    'enabled': True,
    'domain_id': 'default',
    'parent_id': 'default',
    'is_domain': False,
    'tags': [],
    'options': {},
}
