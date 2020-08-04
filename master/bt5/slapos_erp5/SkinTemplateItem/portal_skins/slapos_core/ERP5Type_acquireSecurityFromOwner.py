"""
WARNING: this script requires proxy manager

This script tries to acquire category values from other objects

base_category_list - list of category values we need to retrieve
object             - object which we want to assign roles to.
"""

user_name = ob.Base_getOwnerId() #pylint: disable=redefined-builtin

# XXX Hardcoded role
return {
  'Assignee': [user_name],
}
