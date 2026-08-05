from flask import request, abort, Blueprint, url_for, redirect
from .db import execute_db, decodeSharedParameters
from slapos.util import dict2xml
from six.moves.urllib.parse import unquote, urljoin
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

def _root_instance_list(shared, title=None):
  query = "SELECT * FROM %s WHERE shared=? AND root_instance_guid=''"
  args = [shared]
  if title is not None:
    query += ' AND title=?'
    args.append(title)
  return execute_db('instance', query, args)

def busy_root_partitions_list(title=None):
  partitions = []
  for row in _root_instance_list(0, title=title):
    p = dict(row)
    p['url_string'] = row['software_release']
    p['title'] = row['title']
    p['relative_url'] = url_for('.hateoas_partitions', partition_reference=row['title'])
    partitions.append(p)
  return partitions

def busy_root_shared_list(title=None):
  shared = []
  for row in _root_instance_list(1, title=title):
    s = {}
    s['url_string'] = row['software_release']
    s['title'] = row['title']
    s['relative_url'] = url_for('.hateoas_shared', shared_reference=row['title'])
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
  row = execute_db('instance',
    "SELECT * FROM %s WHERE shared=0 AND root_instance_guid='' AND title=?",
    [partition_reference], one=True)
  if row is None:
    abort(404)
  return hateoas_service_document(
    reference=row['title'],
    requested_state=row['requested_state'],
    xml=row['xml'],
    connection_xml=row['connection_xml'],
    software_release=row['software_release'],
    software_type=row['software_type'],
    shared=0,
  )

@hateoas_blueprint.route('/shared/<shared_reference>', methods=['GET'])
def hateoas_shared(shared_reference):
  row = execute_db('instance',
    "SELECT * FROM %s WHERE shared=1 AND root_instance_guid='' AND title=?",
    [shared_reference], one=True)
  if row is None:
    abort(404)
  return hateoas_service_document(
    reference=shared_reference,
    requested_state='unused',
    # Shared params are stored type-preserving (xml_marshaller); the hateoas
    # my_text_content field is parsed by the client with xml2dict, so re-encode
    # as dict2xml for that consumer.
    xml=dict2xml(decodeSharedParameters(row['xml'])),
    connection_xml=row['connection_xml'],
    software_release=row['software_release'],
    software_type=row['software_type'],
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
