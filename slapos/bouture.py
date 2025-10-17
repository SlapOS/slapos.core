from slapos.util import dumps

computer_dict = dict(reference='COMP-4530', address=None, netmask=None)
computer_dict['partition_list'] = [{'reference': 'slappart3', 'address_list': []}]
slap.registerComputer('COMP-4530').updateConfiguration(dumps(computer_dict))

supply('bogus://sr', 'COMP-4530')

request('bogus://sr', 'bogus-instance')

# /etc/opt/slapos/slapos.cfg
"""
[slapproxy]
host = 127.0.0.1
port = 4000
database_uri = /etc/opt/slapos/slapproxy.db
"""

# /etc/opt/slapos/slapproxy-client.cfg
"""
[slapos]
master_url = http://127.0.0.1:4000
"""

# /etc/opt/slapos# slapos console --cfg slapproxy-client.cfg bouture.py
