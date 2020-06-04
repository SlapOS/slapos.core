"""
  Certificate Login isn't controlled by ERP5 itself
"""

if context.getPassword() in [None, ""]:
  return False

return context.Login_isPasswordExpired()
