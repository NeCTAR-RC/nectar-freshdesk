import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name='nectar-freshdesk',
    version='0.0.1',
    author='Andy Botting',
    author_email='andy@andybotting.com',
    description='Nectar Freshdesk integration',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/NeCTAR-RC/nectar-freshdesk',
    install_requires=requirements,
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'freshdesk-openstack-agent=nectar_freshdesk.openstack.agent:main',
        ]
    },
)
