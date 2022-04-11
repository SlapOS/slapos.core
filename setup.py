from setuptools import setup, find_packages
from shutil import copyfile
import glob
import os
import sys

from slapos.version import version
name = 'slapos.core'
long_description = open("README.rst").read() + "\n" + \
    open("CHANGES.rst").read() + "\n"

for f in sorted(glob.glob(os.path.join('slapos', 'README.*.rst'))):
  long_description += '\n' + open(f).read() + '\n'

slapos_folder_path = os.path.dirname(__file__)
for template_name in ('slapos-client.cfg.example',
    'slapos-proxy.cfg.example', 'slapos.cfg.example'):
  template_path = os.path.join(slapos_folder_path, template_name)
  if os.path.exists(template_path):
    copyfile(template_path,
      os.path.join(slapos_folder_path, 'slapos', template_name))

additional_install_requires = []
# Even if argparse is available in python2.7, some python2.7 installations
# do not have it, so checking python version is dangerous
try:
  import argparse
except ImportError:
  additional_install_requires.append('argparse')

extras_require = {
    'docs': (
        'Sphinx',
        'repoze.sphinx.autointerface',
        'sphinxcontrib.programoutput',
    ),
    'ipython_console': ('ipython',),
    'bpython_console': ('bpython',),
    'test': (
        'pyflakes',
        'mock',
        'httmock',
    ),
}

setup(name=name,
      version=version,
      description="SlapOS core.",
      long_description=long_description,
      classifiers=[
          "Programming Language :: Python",
        ],
      keywords='slapos core',
      license='GPLv3',
      url='https://slapos.nexedi.net',
      author='VIFIB',
      namespace_packages=['slapos'],
      packages=find_packages(),
      include_package_data=True,
      install_requires=[
          'Flask>=1.1.2', # used by proxy
          'lxml', # needed to play with XML trees
          'netaddr>=0.7.5', # to play safely with IPv6 prefixes
          'netifaces', # to fetch information about network devices
          'setuptools', # namespaces
          'supervisor', # slapgrid uses supervisor to manage processes
          'psutil>=2.0.0',
          'xml_marshaller>=0.9.3', # to unmarshall/marshall python objects to/from
                                   # XML
          'zope.interface', # slap library implementes interfaces
          'zc.buildout',
          'cliff',
          'requests>=2.4.3',
          'six',
          'cachecontrol',
          'lockfile',
          'jsonschema',
          'PyYAML',
          'uritemplate', # used by hateoas navigator
          'distro',
          'subprocess32; python_version<"3"',
          'enum34; python_version<"3"',
          'ipaddress; python_version<"3"',  # used by whitelistfirewall
        ] + additional_install_requires,
      extras_require=extras_require,
      tests_require=extras_require['test'],
      zip_safe=False, # proxy depends on Flask, which has issues with
                      # accessing templates
      entry_points={
        'console_scripts': [
          'slapos-watchdog = slapos.grid.watchdog:main',
          'slapos = slapos.cli.entry:main',
        ],
        'cliff.formatter.completion': [
          'fish = slapos.cli.complete:CompleteFish',
        ],
        'slapos.cli': [
          # Utilities
          'cachelookup binary-sr = slapos.cli.cache_binarysr:CacheLookupCommand',
          'cachelookup url = slapos.cli.cache_url:CacheLookupCommand',
          'cachelookup pypi = slapos.cli.cache_pypi:CacheLookupCommand',
          'complete = slapos.cli.complete:CompleteCommand',
          # SlapOS Node commands
          'node bang = slapos.cli.bang:BangCommand',
          'node format = slapos.cli.format:FormatCommand',
          'node register = slapos.cli.register:RegisterCommand',
          'node supervisord = slapos.cli.supervisord:SupervisordCommand',
          'node supervisorctl = slapos.cli.supervisorctl:SupervisorctlCommand',
          'node status = slapos.cli.supervisorctl:SupervisorctlStatusCommand',
          'node start = slapos.cli.supervisorctl:SupervisorctlStartCommand',
          'node stop = slapos.cli.supervisorctl:SupervisorctlStopCommand',
          'node restart = slapos.cli.supervisorctl:SupervisorctlRestartCommand',
          'node tail = slapos.cli.supervisorctl:SupervisorctlTailCommand',
          'node report = slapos.cli.slapgrid:ReportCommand',
          'node software = slapos.cli.slapgrid:SoftwareCommand',
          'node instance = slapos.cli.slapgrid:InstanceCommand',
          'node promise = slapos.cli.slapgrid:PromiseCommand',
          'node boot = slapos.cli.boot:BootCommand',
          'node collect = slapos.cli.collect:CollectCommand',
          'node prune = slapos.cli.prune:PruneCommand',
          # SlapOS client commands
          'console = slapos.cli.console:ConsoleCommand',
          'configure local = slapos.cli.configure_local:ConfigureLocalCommand',
          'configure client = slapos.cli.configure_client:ConfigureClientCommand',
          'service info = slapos.cli.info:InfoCommand',
          'service list = slapos.cli.list:ListCommand',
          'computer list = slapos.cli.computer_list:ListCommand',
          'computer info = slapos.cli.computer_info:InfoCommand',
          'computer token = slapos.cli.computer_token:TokenCommand',
          'supply = slapos.cli.supply:SupplyCommand',
          'remove = slapos.cli.remove:RemoveCommand',
          'request = slapos.cli.request:RequestCommand',
          # SlapOS Proxy commands
          'proxy start = slapos.cli.proxy_start:ProxyStartCommand',
          'proxy show = slapos.cli.proxy_show:ProxyShowCommand',
        ]
      },
      test_suite="slapos.tests",
    )
