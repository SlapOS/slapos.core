from collections import defaultdict

error_list = []
CLIENT_PORTAL_TYPE = 'OAuth2 Authorisation Client Connector'
SERVER_PORTAL_TYPE = 'OAuth2 Authorisation Server Connector'
portal_web_services = context.getPortalObject().portal_web_services
for server_connector_value in portal_web_services.objectValues():
  if (
    server_connector_value.getPortalType() == SERVER_PORTAL_TYPE and
    server_connector_value.getValidationState() == 'validated'
  ):
    break
else:
  # OAuth2 server not configured yet
  server_connector_value = portal_web_services.newContent(
    portal_type=SERVER_PORTAL_TYPE,
    id='slapos_master_oauth2_server',
    title='SlapOS OAuth2 Server',
  )
  server_connector_value.validate()

client_connector_value_dict = defaultdict(list)
for client_connector_value in portal_web_services.objectValues():
  if client_connector_value.getPortalType() == CLIENT_PORTAL_TYPE:
    client_connector_value_dict[
      client_connector_value.getReference()
    ].append(client_connector_value)

rule_dict = {
  # reference          title                 id                 id req. cookie pkce   local access   refresh
  'panelXXXrandom':    ('Panel',             'panelXXXrandom',  True,   False, True,  True,  None,    None),
}

# Check what exists, tolerating some deviations
for client_value in server_connector_value.objectValues():
  client_id = client_value.getId()
  try:
    (
      title,
      client_connector_id,
      client_connector_id_required,
      client_connector_cookie_persistence,
      client_require_pkce,
      client_local,
      _,
      _,
    ) = rule_dict.pop(client_value.getReference())
  except KeyError:
    # unknown client, ignore
    if client_value.getValidationState() == 'validated':
      error_list.append('OAuth2 Client %s: should be invalidated' % (client_id, ))
      if fixit:
        client_value.invalidate()
    continue
  # XXX: It can be acceptable, as long as at least one is validated.
  # But why have multiple client declarations ? So for now, require.
  if client_value.getValidationState() != 'validated':
    error_list.append('OAuth2 Client %s: should be validated' % (client_id, ))
    if fixit:
      client_value.validate()
  if bool(client_value.isProofKeyForCodeExchangeRequired()) != client_require_pkce:
    error_list.append('OAuth2 Client %s: PKCE should be %r' % (client_id, client_require_pkce))
    if fixit:
      client_value.setProofKeyForCodeExchangeRequired(client_require_pkce)
  if bool(client_value.isLocal()) != client_local:
    error_list.append('OAuth2 Client %s: local should be %r' % (client_id, client_local))
    if fixit:
      client_value.setLocal(client_local)
  if client_value.getTitle() != title:
    error_list.append('OAuth2 Client %s: title should be %r' % (client_id, title))
    if fixit:
      client_value.setTitle(title)
  client_connector_value_list = client_connector_value_dict.pop(client_id, [])
  if not client_connector_value_list:
    error_list.append('%s %s: missing' % (CLIENT_PORTAL_TYPE, client_id, ))
    if fixit:
      portal_web_services.newContent(
        portal_type=CLIENT_PORTAL_TYPE,
        id=client_connector_id,
        reference=client_id,
        title=title,
        authorisation_server_url=server_connector_value.getId(),
        cookie_persistence=client_connector_cookie_persistence,
      ).validate()
    continue
  try:
    client_connector_value, = client_connector_value_list
  except ValueError:
    error_list.append(
      'Too many %s with reference %r, CANNOT AUTOMATICALLY RECOVER' % (
        CLIENT_PORTAL_TYPE,
        client_id,
      ),
    )
    continue
  if client_connector_value.getValidationState() != 'validated':
    error_list.append(
      '%s %s: should be validated' % (
        CLIENT_PORTAL_TYPE,
        client_id,
      ),
    )
    if fixit:
      client_connector_value.validate()
  if client_connector_id_required and client_connector_value.getId() != client_connector_id:
    error_list.append(
      '%s %s: must have id %r, not %r' % (
        CLIENT_PORTAL_TYPE,
        client_id,
        client_connector_id,
        client_connector_value.getId(),
      ),
    )
    if fixit:
      client_connector_value.setId(client_connector_id)

# Create what is missing
for client_reference, (
  title,
  client_connector_id,
  _,
  client_connector_cookie_persistence,
  client_require_pkce,
  client_local,
  client_access_token_lifespan,
  client_refresh_token_lifespan,
) in rule_dict.items():
  error_list.append('OAuth2 Client %s: missing' % (
    client_reference,
  ))
  if fixit:
    client_value = server_connector_value.newContent(
      portal_type='OAuth2 Client',
      title=title,
      proof_key_for_code_exchange_required=client_require_pkce,
      local=client_local,
      client_access_token_lifespan=client_access_token_lifespan,
      refresh_token_lifespan=client_refresh_token_lifespan,
      reference=client_reference,
    )
    client_value.validate()
    portal_web_services.newContent(
      portal_type=CLIENT_PORTAL_TYPE,
      id=client_connector_id,
      title=title,
      reference=client_value.getId(),
      authorisation_server_url=server_connector_value.getId(),
      cookie_persistence=client_connector_cookie_persistence,
    ).validate()

# Remove unexpected client connectors
for _, client_connector_value_list in client_connector_value_dict.items():
  for client_connector_value in client_connector_value_list:
    if client_connector_value.getValidationState() == 'validated':
      error_list.append('OAuth2 Client Connector %s: should be invalidated' % (client_connector_value.getId(), ))
      if fixit:
        client_connector_value.invalidate()

return error_list
