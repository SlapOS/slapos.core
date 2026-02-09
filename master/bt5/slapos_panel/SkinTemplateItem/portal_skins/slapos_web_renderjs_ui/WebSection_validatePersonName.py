import re

FORBIDDEN_CHAR = re.compile("["
  "/"
  "?"
  "@"
  "#"
"]+")

return not (('http' in value) or
            (re.search(FORBIDDEN_CHAR, value)))
