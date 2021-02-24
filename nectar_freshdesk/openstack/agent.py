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

import time

from oslo_log import log

from nectar_freshdesk import config

from nectar_freshdesk.openstack import clients
from nectar_freshdesk.openstack import freshdesk
from nectar_freshdesk.openstack import messaging
from nectar_freshdesk.openstack import utils

from nectar_freshdesk.openstack.resource import instance
from nectar_freshdesk.openstack.resource import project
from nectar_freshdesk.openstack.resource import role
from nectar_freshdesk.openstack.resource import user
from nectar_freshdesk.openstack.resource import volume


CONF = config.CONF
LOG = log.getLogger(__name__)


class FreshDeskOpenStackEndpoint(object):

    def info(self, ctxt, info):
        LOG.info('Processing ticket')
        details = []
        try:
            # Test for required fields
            if not all(f in info for f in config.REQUIRED_FIELDS):
                missing = [f for f in config.REQUIRED_FIELDS if f not in info]
                raise KeyError('Required field(s) missing: %s', missing)

            # Get ticket
            fd = freshdesk.get_freshdesk_client()
            ticket_id = int(info.get('ticket_id'))
            ticket = fd.tickets.get_ticket(ticket_id)
            tags = []

            # Process user info on ticket create only
            if info.get('action') == 'create':
                email = info.get('email')
                if email:
                    # User information
                    LOG.info("Fetching user information for %s", email)
                    user_info = user.get_user(email)
                    if user_info:
                        details.append(user_info)

                    LOG.info("Fetching role information for %s", email)
                    role_info = role.get_roles(email)
                    if role_info:
                        details.append(role_info)

            if config.PROCESSED_TAG in ticket.tags:
                LOG.info("Already processed ticket %s", ticket_id)
            else:
                source = info.get('source')

                # Instance information by UUID
                uuids = utils.find_uuids(source)
                LOG.info("Found UUIDs in ticket: %s", uuids)

                # Instance information by IPv4
                ipv4s = utils.find_ipv4s(source)
                LOG.info("Found IPv4 addresses in ticket: %s", ipv4s)

                for ipv4 in ipv4s:
                    # Resolve instance IDs and add to list
                    for ins in clients.list_instances(ip=ipv4):
                        # Nova does a greedy regex so we just need to confirm
                        # our instance actually does have the address we want
                        if ipv4 in [y['addr'] for x in ins.addresses.values()
                                    for y in x]:
                            uuids.append(ins.id)

                for uuid in set(uuids):
                    uuid_info = self.process_uuid(uuid)
                    if uuid_info:
                        details.append(uuid_info)

                if uuids:
                    # Flag as processed if we have found any uuids
                    tags.append(config.PROCESSED_TAG)
            if details:
                LOG.info("Creating note for ticket %s", ticket_id)
                output = '<br>'.join(details)
                fd.comments.create_note(ticket_id, output)

            # Update ticket with processes tag
            if tags:
                tags = list(set(tags + ticket.tags))
                LOG.info("Updating ticket with tags: %s", tags)
                fd.tickets.update_ticket(ticket_id, tags=tags)

        except Exception as e:
            LOG.exception(e)
            LOG.error(info)

    def process_uuid(self, uuid):
        LOG.info("Getting information for: %s", uuid)
        uuid_info = instance.get_instance(uuid)
        if uuid_info:
            return uuid_info

        uuid_info = volume.get_volume(uuid)
        if uuid_info:
            return uuid_info

        uuid_info = project.get_project(uuid)
        if uuid_info:
            return uuid_info


class Agent(object):
    def __init__(self):
        endpoint = FreshDeskOpenStackEndpoint()
        server = messaging.get_rpc_server(endpoint)
        self.server = server

    def run(self):
        try:
            self.server.start()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            LOG.info('Stopping agent')

        self.server.stop()
        self.server.wait()
