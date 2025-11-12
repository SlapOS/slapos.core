from werkzeug.routing import BaseConverter


class AbsolutePathConverter(BaseConverter):
    """Like the default :class:`UnicodeConverter`, but it also matches
    slashes. Requires to start with a slash
    """

    part_isolating = False
    regex = "/.*?"
    weight = 300
