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

import setuptools

from pbr.packaging import parse_requirements

setuptools.setup(
    name='nectar-freshdesk',
    version='0.0.1',
    author='Andy Botting',
    author_email='andy@andybotting.com',
    description='Nectar Freshdesk integration',
    url='https://github.com/NeCTAR-RC/nectar-freshdesk',
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'nectar-freshdesk = nectar_freshdesk.cmd.api:main',
            'nectar-freshdesk-agent = nectar_freshdesk.cmd.agent:main',
        ],
        'oslo.config.opts': [
            'nectar-freshdesk = nectar_freshdesk.config:list_opts',
        ],
    },
    include_package_data=True,
    setup_requires=['pbr>=3.0.0'],
    install_requires=parse_requirements(),
    license="Apache",
    zip_safe=False,
)
