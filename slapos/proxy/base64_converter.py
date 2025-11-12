from werkzeug.routing import BaseConverter, ValidationError
from base64 import urlsafe_b64encode, urlsafe_b64decode
from urllib.parse import unquote_plus
from binascii import Error as binasciiError


def b64e(bytes_value):
  return urlsafe_b64encode(bytes_value).decode()


class Base64Converter(BaseConverter):
  def to_python(self, bytes_value):
    try:
      return urlsafe_b64decode(unquote_plus(bytes_value))
    except binasciiError:
      raise ValidationError()

  def to_url(self, bytes_value):
    return b64e(bytes_value)
