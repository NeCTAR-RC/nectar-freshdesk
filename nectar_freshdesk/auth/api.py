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

JWT_PARAMS = ['nonce', 'state', 'client_id']

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET'])
def login():
    if all(p in request.args for p in JWT_PARAMS):
        for p in JWT_PARAMS:
            session[p] = request.args.get(p)
    return redirect(CONF.auth.aaf_login_url)


@bp.route('/cb', methods=['POST'])
def callback():
    try:
        jwt_secret = CONF.auth.aaf_secret
        audience = CONF.auth.service_url
        assertion = request.form.get('assertion')
        verified_jwt = jwt.decode(assertion, jwt_secret,
                                  audience=audience, algorithms='HS256')
        attrs = verified_jwt['https://aaf.edu.au/attributes']

        if all(p in session for p in JWT_PARAMS):
            return freshdesk_jwt(attrs)
        else:
            return freshdesk_simple_sso(attrs)

    except jwt.ExpiredSignature:
        return make_response('Expired Signature', 400)


def freshdesk_simple_sso(attrs):
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


def freshdesk_jwt(attrs):
    key_file = CONF.freshdesk.sso_key

    # Should match Redirect URL as prescribed in FD SSO settings
    url = "{}/sp/OIDC/{}/implicit".format(
              CONF.freshdesk.sso_url, session['client_id'])

    # Freshdesk required params
    # https://support.freshworks.com/support/solutions/articles/50000000670-how-to-configure-sso-with-custom-jwt-implementation
    payload = {
        'sub': attrs.get('edupersonprincipalname'),
        'name': attrs.get('displayname'),
        'given_name': attrs.get('givenname'),
        'family_name': attrs.get('surname'),
        'email': attrs.get('mail'),
        'iat': str(int(time.time())),
        'nonce': session['nonce'],
    }

    with open(key_file) as key:
        id_token = jwt.encode(payload, key.read(), algorithm='RS256')

    params = {
        'state': session['state'],
        'id_token': id_token,
    }
    result = '{}?{}'.format(url, urllib.parse.urlencode(params))
    return redirect(result)
