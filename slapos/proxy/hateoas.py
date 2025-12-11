from flask import request, abort, Blueprint, url_for, redirect
from .db import execute_db, getRootPartitionList, getRootSharedList
from six.moves.urllib.parse import unquote, urljoin
from slapos.util import loads, dict2xml
import re

hateoas_blueprint = Blueprint('hateoas', __name__)


# hateoas routing
# ---------------

# We only need to handle the hateoas requests made by
#   slapos service list
#   slapos service info <reference>
#   slapos computer list
#   slapos computer info <reference>


def unquoted_url_for(method, **kwargs):
  return unquote(url_for(method, **kwargs))

def busy_root_partitions_list(title=None):
  partitions = []
  for row in getRootPartitionList(title=title):
    p = dict(row)
    p['url_string'] = p['software_release']
    p['title'] = p['partition_reference']
    p['relative_url'] = url_for('.hateoas_partitions', partition_reference=p['partition_reference'])
    partitions.append(p)
  return partitions

def busy_root_shared_list(title=None):
  shared = []
  for row in getRootSharedList(title=title):
    host = execute_db('partition', 'SELECT * FROM %s WHERE reference=?', [row['hosted_by']], one=True)
    if not host:
      continue
    for slave_dict in loads(host['slave_instance_list'].encode('utf-8')):
      if slave_dict['slave_reference'] == row['reference']:
        break
    else:
      continue
    s = {}
    s['url_string'] = host['software_release']
    s['title'] = row['reference'][1:] # root shared are prefixed with _
    s['relative_url'] = url_for('.hateoas_shared', shared_reference=s['title'])
    shared.append(s)
  return shared

def computers_list(reference=None):
  computers = []
  query = 'SELECT * FROM %s'
  args = []
  if reference:
    query += ' WHERE reference=?'
    args.append(reference)
  for row in execute_db('computer', query, args):
    c = dict(row)
    c['title'] = c['reference']
    c['relative_url'] = url_for('.hateoas_computers', computer_reference=c['reference'])
    computers.append(c)
  return computers

r_string = re.compile('"((\\.|[^\\"])*)"')

def is_valid(name):
  match = r_string.match(name)
  if match.group(0) == name:
    return True
  return False

p_service_list = 'portal_type:"Instance Tree" AND validation_state:validated'
p_service_info = p_service_list + ' AND title:='
p_computer_list = 'portal_type:"Compute Node" AND validation_state:validated'
p_computer_info = p_computer_list + ' AND reference:='

def parse_query(query):
  if query == p_service_list:
    return busy_root_partitions_list() + busy_root_shared_list()
  elif query.startswith(p_service_info):
    title = query[len(p_service_info):]
    if is_valid(title):
      partition = busy_root_partitions_list(title.strip('"'))
      if partition:
        return partition
      return busy_root_shared_list(title.strip('"'))
  elif query == p_computer_list:
    return computers_list()
  elif query.startswith(p_computer_info):
    reference = query[len(p_computer_info):]
    if is_valid(reference):
      return computers_list(reference.strip('"'))
  return None

@hateoas_blueprint.route('/partitions/<partition_reference>', methods=['GET'])
def hateoas_partitions(partition_reference):
  partition = execute_db('partition', 'SELECT * FROM %s WHERE partition_reference=?', [partition_reference], one=True)
  if partition is None:
    abort(404)
  partition['reference'] = partition['partition_reference']
  partition['shared'] = 0
  return hateoas_service_document(**partition)

@hateoas_blueprint.route('/shared/<shared_reference>', methods=['GET'])
def hateoas_shared(shared_reference):
  slave_reference = '_' + shared_reference # root shared are prefixed with _ in db
  shared = execute_db('slave', 'SELECT * FROM %s WHERE reference=?', [slave_reference], one=True)
  if shared is None:
    abort(404)
  partition = execute_db('partition', 'SELECT * FROM %s WHERE reference=?', [shared['hosted_by']], one=True)
  if partition is None:
    abort(404)
  slave_list = loads(partition['slave_instance_list'].encode('utf-8'))
  for slave_dict in slave_list:
    if slave_dict['slave_reference'] == slave_reference:
      break
  else:
    abort(404)
  del slave_dict['slave_title'], slave_dict['slave_reference']
  software_type = slave_dict.pop('slap_software_type')
  xml = dict2xml(slave_dict)
  return hateoas_service_document(
    reference = shared_reference,
    requested_state='unused',
    xml=xml,
    connection_xml=shared['connection_xml'],
    software_release=partition['software_release'],
    software_type=software_type,
    shared=1,
  )

def hateoas_service_document(**kw):
  # my_slap_state corresponds to requested_state, not slap_state.
  return {
    '_embedded': {
      '_view': {
        'form_id': {
          'type': 'StringField',
          'key': 'form_id',
          'default': 'InstanceTree_viewAsHateoas',
        },
        'my_reference': {
          'type': 'StringField',
          'key': 'field_my_reference',
          'default': kw['reference'],
        },
        'my_slap_state': {
          'type': 'StringField',
          'key': 'field_my_slap_state',
          'default': kw['requested_state'],
        },
        'my_text_content': {
          'type': 'StringField',
          'key': 'field_my_text_content',
          'default': kw['xml'],
        },
        'my_connection_parameter_list': {
          'type': 'StringField',
          'key': 'field_my_connection_parameter_list',
          'default': kw['connection_xml'],
        },
        'my_url_string': {
          'type': 'StringField',
          'key': 'field_my_url_string',
          'default': kw['software_release'],
        },
        'my_source_reference': {
          'type': 'StringField',
          'key': 'field_my_source_reference',
          'default': kw['software_type'],
        },
        'my_root_slave': {
          'type': 'IntegerField',
          'key': 'field_my_root_slave',
          'default': kw['shared'],
        },
      },
    },
    '_links': {
      'type': {
        'name': 'Instance Tree',
      },
    },
  }

@hateoas_blueprint.route('/computers/<computer_reference>', methods=['GET'])
def hateoas_computers(computer_reference):
  computer = execute_db('computer', 'SELECT * FROM %s WHERE reference=?', [computer_reference], one=True)
  if computer is None:
    abort(404)
  return {
    '_embedded': {
      '_view': {
        'form_id': {
          'type': 'StringField',
          'key': 'computer',
          'default': computer['reference'],
        },
        'my_reference': {
          'type': 'StringField',
          'key': 'reference',
          'default': computer['reference'],
        },
        'my_title': {
          'type': 'StringField',
          'key': 'reference',
          'default': computer['reference'],
        },
      },
    },
    '_links': {
      'type': {
        'name': 'Computer',
      },
    },
  }

def hateoas_traverse():
  return redirect(request.args['relative_url'])

def hateoas_search():
  contents = parse_query(request.args["query"])
  if contents is None:
    abort(400, "Unhandled query: %s" % request.args["query"])
  return { '_embedded': {'contents': contents} }

def hateoas_root():
  return {
    '_links': {
      'raw_search': {
      'href': urljoin(request.host_url, unquoted_url_for('.hateoas', mode='search', query='{query}', select_list='{select_list}'))
    },
      'traverse': {
        'href': urljoin(request.host_url, unquoted_url_for('.hateoas', mode='traverse', relative_url='{relative_url}', view='{view}'))
      },
    }
  }

mode_handlers = {
  None: hateoas_root,
  'search': hateoas_search,
  'traverse': hateoas_traverse,
}

@hateoas_blueprint.route('/', methods=['GET'])
def hateoas():
  mode = request.args.get('mode')
  handler = mode_handlers.get(mode, lambda: abort(400, "Unhandled mode: %s" % mode))
  resp = handler()
  return resp
