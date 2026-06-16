"""
  External Validator that checks that request body is not to big
  See Ticket_addSlapOSEvent and Base_addSlapOSSupportRequest
"""
return int(request.getHeader('Content-Length', 0)) < 3145728
