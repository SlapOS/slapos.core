import zope.interface
from interface import slap as interface

class ResourceNotReady(Exception):
  zope.interface.implements(interface.IResourceNotReady)

class ServerError(Exception):
  zope.interface.implements(interface.IServerError)

class NotFoundError(Exception):
  zope.interface.implements(interface.INotFoundError)

class AuthenticationError(Exception):
  pass

class ConnectionError(Exception):
  zope.interface.implements(interface.IConnectionError)
