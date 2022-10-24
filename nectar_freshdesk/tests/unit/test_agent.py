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

from unittest import mock

from nectar_freshdesk import config
from nectar_freshdesk.tests.unit import base
from nectar_freshdesk.tests.unit import fakes

from nectar_freshdesk.openstack.agent import FreshDeskOpenStackEndpoint


@mock.patch('nectar_freshdesk.openstack.resource.instance.get_instance')
@mock.patch('nectar_freshdesk.openstack.resource.project.get_project')
@mock.patch('nectar_freshdesk.openstack.resource.role.get_roles')
@mock.patch('nectar_freshdesk.openstack.resource.user.get_user')
@mock.patch('nectar_freshdesk.openstack.resource.volume.get_volume')
@mock.patch('nectar_freshdesk.openstack.freshdesk.get_freshdesk_client')
class TestFreshDeskOpenStackEndpoint(base.TestCase):

    def test_info_raise_missing_fields(self, mock_freshdeskclient,
                                       mock_get_volume, mock_get_user,
                                       mock_get_roles, mock_get_project,
                                       mock_get_instance):
        info = {}
        endpoint = FreshDeskOpenStackEndpoint()
        endpoint.info(None, info)
        self.assertRaises(KeyError)

    def test_create_ticket_add_info_no_uuid(
            self, mock_freshdeskclient, mock_get_volume, mock_get_user,
            mock_get_roles, mock_get_project, mock_get_instance):

        fd = mock_freshdeskclient.return_value
        ticket = fd.tickets.get_ticket.return_value
        ticket.tags = [config.PROCESSED_TAG]

        mock_get_user.return_value = 'user'
        mock_get_roles.return_value = 'roles'

        endpoint = FreshDeskOpenStackEndpoint()

        # Call the processing function
        endpoint.info(None, fakes.TICKET_WEBHOOK_INFO)
        fd.comments.create_note.assert_called_once_with(1234, 'user<br>roles')

    def test_create_ticket_add_info_uuid(
            self, mock_freshdeskclient, mock_get_volume, mock_get_user,
            mock_get_roles, mock_get_project, mock_get_instance):

        fd = mock_freshdeskclient.return_value
        ticket = fd.tickets.get_ticket.return_value
        ticket.tags = []

        mock_get_user.return_value = 'user'
        mock_get_roles.return_value = 'roles'
        mock_get_instance.return_value = 'instance'

        endpoint = FreshDeskOpenStackEndpoint()

        info = fakes.TICKET_WEBHOOK_INFO
        info['source'] = 'Some f6933a0aa39b400dacf65909b38cc3d9 UUID'

        # Call the processing function
        endpoint.info(None, info)

        fd.comments.create_note.assert_called_once_with(
            1234, 'user<br>roles<br>instance')
        fd.tickets.update_ticket.assert_called_once_with(
            1234, tags=[config.PROCESSED_TAG])

    def test_update_ticket_already_processed(
            self, mock_freshdeskclient, mock_get_volume, mock_get_user,
            mock_get_roles, mock_get_project, mock_get_instance):

        fd = mock_freshdeskclient.return_value

        # Already processed flag
        ticket = fd.tickets.get_ticket.return_value
        ticket.tags = [config.PROCESSED_TAG]

        endpoint = FreshDeskOpenStackEndpoint()

        info = fakes.TICKET_WEBHOOK_INFO
        info['action'] = 'update'
        info['source'] = 'Some f6933a0aa39b400dacf65909b38cc3d9 UUID'

        # Call the processing function
        endpoint.info(None, info)

        fd.comments.create_note.assert_not_called()
        fd.tickets.update_ticket.assert_not_called()
