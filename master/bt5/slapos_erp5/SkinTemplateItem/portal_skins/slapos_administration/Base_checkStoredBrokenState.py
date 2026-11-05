# Ensure object is loaded
context.getTitle()

# Ensure broken state is not stored
show_dict = context.showDict()
assert '__Broken_state__' not in show_dict
assert '__Broken_newargs__' not in show_dict
