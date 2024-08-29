from DateTime import DateTime

now = int(DateTime())

return {
  'customer_login': 'testcustomer%s' % now,
  'remote_customer_login': 'testremotecustomer%s' % now,
  'manager_login': 'testmanager%s' % now,
  'passwd': 'eiChaxo5Eefier9vAek7phie$%s' % now,
  'project_title': 'TestProject%s' % now
}
