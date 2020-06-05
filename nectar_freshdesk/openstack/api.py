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

from flask import Blueprint
from flask import jsonify
from flask import make_response
from flask import request

from oslo_context import context
from oslo_log import log

from nectar_freshdesk import config
from nectar_freshdesk.openstack import messaging


CONF = config.CONF
OSLO_CONTEXT = context.RequestContext()
LOG = log.getLogger(__name__)

bp = Blueprint('api', __name__)


@bp.route('/addinfo', methods=['POST'])
def addinfo():
    info = request.json

    # Test valid request
    if not all(f in info for f in config.REQUIRED_FIELDS):
        missing = [f for f in config.REQUIRED_FIELDS if f not in info]
        error = 'Required field(s) missing from request: %s' % missing
        LOG.warning(error)
        return make_response(jsonify(error=error), 422)

    client = messaging.get_rpc_client()
    client.cast(OSLO_CONTEXT, 'info', info=info)
    return jsonify(success=True)
