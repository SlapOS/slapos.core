# This script hardcoded inside slapgrid is fully deprecated
# as a compute node token MUST be associated to a project
# which means a project reference parameter is REQUIRED
# for now, this is not possible to do, as the client hardcode the url...

import json
context.RESPONSE.setStatus(410)
return json.dumps({'message': 'This API is no longer supported'})
