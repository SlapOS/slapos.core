""" Simple place for keep the list of business template to install on this project
"""
bt5_update_catalog_list = (
   'erp5_web_shadir',
   'erp5_syncml',
   'erp5_ingestion_mysql_innodb_catalog',
   'erp5_wendelin',
   'slapos_mysql_innodb_catalog'
)
bt5_installation_list = bt5_update_catalog_list + ('slapos_erp5',)

keep_bt5_id_list = ['erp5_ui_test',
                    'erp5_ui_test_core',
                    # XXX erp5_accounting_l10n_fr should be removed when bug is fixed
                    'erp5_accounting_l10n_fr',
                    'erp5_secure_payment',
                    'slapos_hypermedia',
                    'vifib_datas']

return bt5_installation_list, bt5_update_catalog_list, keep_bt5_id_list
