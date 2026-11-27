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

import html

from oslo_config import cfg
from oslo_log import log

from nectar_freshdesk import config
from nectar_freshdesk.openstack import agent
from nectar_freshdesk.openstack import freshdesk
from nectar_freshdesk.openstack import messaging
from nectar_freshdesk.triage import client


CONF = cfg.CONF
LOG = log.getLogger(__name__)

NOTE_HEADER = (
    '<b>AI triage</b> (generated automatically, check before relying on it)'
)


class TriageEndpoint:
    def triage(self, ctxt, info):
        try:
            self._triage(info)
        except Exception as e:
            # A failed triage leaves the ticket as it was
            LOG.exception(e)
            LOG.error('Triage failed for ticket %s', info.get('ticket_id'))

    def _triage(self, info):
        action = info.get('action')
        if not CONF.triage.enabled or action not in CONF.triage.actions:
            LOG.info('Triage not enabled for action %s', action)
            return

        fd = freshdesk.get_freshdesk_client()
        ticket_id = int(info['ticket_id'])
        ticket = fd.tickets.get_ticket(ticket_id)
        if config.TRIAGE_TAG in ticket.tags:
            LOG.info('Already triaged ticket %s', ticket_id)
            return

        # Only the ticket ID is sent. The agent reads the ticket with its
        # own read-only Freshdesk access.
        LOG.info('Requesting triage of ticket %s', ticket_id)
        text = client.triage(
            f'Triage Freshdesk ticket {ticket_id}.',
            f'nectar-freshdesk-{ticket_id}-{action}',
        )

        # The agent's answer is untrusted, it has read text written by the
        # ticket's author. It only ever becomes an escaped private note.
        body = html.escape(text).replace('\n', '<br>')
        LOG.info('Creating triage note for ticket %s', ticket_id)
        fd.comments.create_note(
            ticket_id, f'{NOTE_HEADER}<br><br>{body}', private=True
        )

        # Tags may have changed while the agent was working
        ticket = fd.tickets.get_ticket(ticket_id)
        tags = list(set(ticket.tags + [config.TRIAGE_TAG]))
        fd.tickets.update_ticket(ticket_id, tags=tags)


class Worker(agent.Agent):
    def __init__(self):
        self.server = messaging.get_rpc_server(
            TriageEndpoint(), messaging.get_triage_target()
        )
