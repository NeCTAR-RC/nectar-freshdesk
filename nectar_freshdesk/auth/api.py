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

import hashlib
import hmac
import jwt
import time
import urllib

from flask import Blueprint
from flask import make_response
from flask import redirect
from flask import request
from flask import session

from oslo_context import context
from oslo_log import log

from nectar_freshdesk import config

CONF = config.cfg.CONF
OSLO_CONTEXT = context.RequestContext()
LOG = log.getLogger(__name__)

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/sso')
def index():
    return redirect(CONF.auth.aaf_login_url)


@bp.route('/login', methods=['POST'])
def login():
    try:
        jwt_secret = CONF.auth.aaf_secret
        assertion = request.form.get('assertion')

        audience = CONF.auth.service_url

        verified_jwt = jwt.decode(assertion, jwt_secret,
                                  audience=audience, algorithms='HS256')

        session['attributes'] = verified_jwt['https://aaf.edu.au/attributes']

        attrs = verified_jwt['https://aaf.edu.au/attributes']

        session['attributes'] = attrs
        session['jwt'] = verified_jwt
        session['jws'] = assertion

        url = CONF.freshdesk.sso_url
        key = CONF.freshdesk.sso_key

        name = attrs.get('cn')
        email = attrs.get('mail')
        ts = str(int(time.time()))

        # Freshdesk special string uses for the signature
        hash_source = name + key + email + ts
        hash_digest = hmac.new(key.encode(),
                               hash_source.encode(),
                               hashlib.md5).hexdigest()
        params = {
            'name': name,
            'email': email,
            'timestamp': ts,
            'hash': hash_digest,
        }
        result = '{}?{}'.format(url, urllib.parse.urlencode(params))
        return redirect(result)
    except jwt.ExpiredSignature:
        return make_response('expired')
