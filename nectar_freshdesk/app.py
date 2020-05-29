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

import flask

from nectar_freshdesk.auth import api as auth
from nectar_freshdesk import config
from nectar_freshdesk.openstack import api as openstack

from oslo_middleware import healthcheck


CONF = config.CONF


def create_app(conf_file=None, init_config=True):
    # create and configure the app
    if init_config:
        if conf_file:
            config.init(conf_file=conf_file)
        else:
            config.init()

    app = flask.Flask(__name__)

    config.setup_logging(CONF)

    # Secret key for Flask sessions
    app.secret_key = CONF.flask.secret_key

    # OSLO healthcheck middleware
    app.wsgi_app = healthcheck.Healthcheck(app.wsgi_app)

    # Apps
    app.register_blueprint(openstack.bp)
    app.register_blueprint(auth.bp)

    return app
