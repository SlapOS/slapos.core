from DateTime import DateTime
from zExceptions import Unauthorized
if REQUEST is not None:
  raise Unauthorized

return [i.getReference()
             for i in context.portal_simulation.getCurrentTrackingList(
               **{"project_uid": context.getUid(), "at_date": DateTime()})]
