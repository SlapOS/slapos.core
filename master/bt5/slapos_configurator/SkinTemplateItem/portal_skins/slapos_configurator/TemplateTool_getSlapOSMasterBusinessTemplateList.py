""" Simple place for keep the list of business template to install on this project
"""
bt5_installation_list = ('slapos_erp5',)
bt5_update_catalog_list = bt5_installation_list

keep_bt5_id_list = ['erp5_ui_test',
                    'erp5_ui_test_core',
                    'slapos_jio_ui_test',
                    # XXX erp5_accounting_l10n_fr should be removed when bug is fixed
                    'erp5_accounting_l10n_fr',
                    'erp5_secure_payment',
                    'slapos_hypermedia',
                    'vifib_datas']

return bt5_installation_list, bt5_update_catalog_list, keep_bt5_id_list
