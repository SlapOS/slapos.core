# This script might not be efficient to a large quantities of
# Compute Nodes
from DateTime import DateTime
import json
kw = {"project_uid": context.getUid(),
      "at_date": DateTime(),
      "limit": 1}

return json.dumps(len(context.portal_simulation.getCurrentTrackingList(**kw)))
