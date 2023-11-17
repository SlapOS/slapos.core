# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Nexedi SA and Contributors. All Rights Reserved.
#                    Romain Courteaud <romain@nexedi.com>
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from erp5.component.test.SlapOSTestCaseMixin import SlapOSTestCaseMixin
import difflib

slapos_folder_list = """slapos_abyss
slapos_base
slapos_contract
slapos_subscription_request
slapos_crm_monitoring
slapos_accounting
slapos_administration
slapos_cloud
slapos_consumption
slapos_core
slapos_crm
slapos_payzen
slapos_pdm
slapos_simulation
slapos_slap_tool
slapos_wechat
slapos_configurator"""

common2_folder_list = """erp5_accounting_l10n_fr
erp5_certificate_authority
erp5_item
erp5_item_trade
erp5_oauth2_resource
erp5_upgrader
erp5_access_tab
erp5_access_token
erp5_accounting
erp5_accounting_eu
erp5_accounting_fr
erp5_administration
erp5_authentication_policy
erp5_auto_logout
erp5_base
erp5_bearer_token
erp5_big_file
erp5_ckeditor
erp5_code_mirror
erp5_commerce
erp5_commerce_widget_library
erp5_computer_immobilisation
erp5_configurator
erp5_configurator_wizard
erp5_content_translation
erp5_core
erp5_core_proxy_field_legacy
erp5_corporate_identity"""

common3_folder_list = """erp5_credential
erp5_credential_oauth2
erp5_crm
erp5_data_notebook
erp5_data_set
erp5_deferred_style_core
erp5_development
erp5_dhtml_style
erp5_diff
erp5_dms
erp5_fckeditor
erp5_forge
erp5_forge_release
erp5_gadget
erp5_glossary
erp5_graph_editor"""

common_folder_list = """erp5_jquery_sheet_editor
erp5_json_editor
erp5_json_type
erp5_monaco_editor
erp5_multimedia
erp5_notebook
erp5_oauth
erp5_oauth_facebook_login
erp5_oauth_google_login
erp5_ods_core
erp5_odt_core
erp5_officejs_bookmark_manager
erp5_officejs_drive
erp5_officejs_media_player
erp5_officejs_slideshow_editor
erp5_officejs_smart_assistant
erp5_ooo_import
erp5_open_trade
erp5_payzen_secure_payment
erp5_pdm
erp5_project
erp5_project_trade
erp5_rss_core
erp5_run_my_doc
erp5_secure_payment
erp5_simplified_invoicing
erp5_slideshow_core
erp5_smart_assistant
erp5_smart_assistant_file
erp5_smart_assistant_image
erp5_smart_assistant_sound
erp5_smart_assistant_text
erp5_software_pdm
erp5_svg_editor
erp5_syncml
erp5_system_event
erp5_toolbox
erp5_trade
erp5_vcs
erp5_web
erp5_web_crm
erp5_web_minimal_theme
erp5_web_renderjs
erp5_web_service
erp5_web_widget_library
erp5_wechat_secure_payment
erp5_wendelin
erp5_wendelin_notebook"""

class TestSlaposSkinSelectionMixin(SlapOSTestCaseMixin):
  # Ignore these bt5 as they might be present on development instances
  # but not present on the test.
  ignore_list = [
    # UI testing folders not deployed by Configurator
    "slapos_ui_test"]

  expected_available_skin = [
          'AppCache',
          'Contract',
          'Leaflet',
          'Release',
          'Slide',
          'Book',
          'CI_web',
          'Letter',
          'Report',
          'Deferred',
          'Deploy',
          'Download',
          'Hal',
          'HalRestricted',
          'KM',
          'Multiflex',
          'ODS',
          'ODT',
          'RJS',
          'RSS',
          'RedirectAssist',
          'SHACACHE',
          'SHADIR',
          'SlapOSHalRestricted',
          'SlideShow',
          'View'
        ]

  redirect_assistant_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_web_redirect_assist
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
    } 

  deffered_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
erp5_credential
erp5_credential_oauth2
erp5_crm
erp5_data_notebook
erp5_data_set
erp5_deferred_style
erp5_deferred_style_core
erp5_development
erp5_dhtml_style
erp5_diff
erp5_dms
erp5_fckeditor
erp5_forge
erp5_forge_release
erp5_gadget
erp5_glossary
erp5_graph_editor
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
    }


  deploy_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
slapos_deploy_theme
erp5_web_hal_json
erp5_web_renderjs_ui
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      }

  view_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_web_officejs_ui
erp5_xhtml_disabled
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_html_compatibility
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
erp5_jquery
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      }

  km_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_km_theme
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
erp5_jquery
erp5_jquery_sheet_editor
erp5_json_editor
erp5_json_type
erp5_km_widget_library
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : '\n'.join(common_folder_list.split('\n')[4:]),
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      }

  multiflex_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_commerce_multiflex_layout
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      }

  download_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_web_download_theme
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      }

  ods_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
erp5_ods_style
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      }

  odt_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
erp5_odt_style
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      }

  rss_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
slapos_rss_style
%(slapos_folder_list)s
erp5_rss_style
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      }

  shadir_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_web_shadir
erp5_km
erp5_web_download_theme
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      }

  shacache_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_web_shacache
erp5_km
erp5_web_download_theme
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      }

  rjs_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
slapos_hal_json_style
erp5_web_hal_json
erp5_web_renderjs_ui
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_web_officejs_ui
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      }

  slapos_hal_restricted_selection_string_list = \
"""
custom
erp5_font
slapos_hal_json_restricted_compatibility_style
erp5_interaction_drop
erp5_hal_json_restricted_style
erp5_hal_json_style
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      }


  appcache_selection_string_list = """custom
erp5_font
erp5_interaction_drop
erp5_hal_json_style
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_web_redirect_assist
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      } 

  leaflet_selection_string_list = """custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
erp5_corporate_identity_leaflet
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      } 

  release_selection_string_list = """custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
erp5_corporate_identity_release
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      } 

  slide_selection_string_list = """custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
erp5_corporate_identity_slide
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      } 


  slideshow_selection_string_list = """custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
slapos_abyss
slapos_base
slapos_contract
slapos_subscription_request
slapos_crm_monitoring
slapos_accounting
slapos_administration
slapos_cloud
slapos_consumption
slapos_core
slapos_crm
slapos_payzen
slapos_pdm
slapos_simulation
slapos_slap_tool
slapos_wechat
erp5_slideshow_style
slapos_configurator
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      } 

  book_selection_string_list = """custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
erp5_corporate_identity_book
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      } 

  ci_web_selection_string_list = """custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
erp5_corporate_identity_web
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      } 

  letter_selection_string_list = """custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
erp5_corporate_identity_letter
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      } 

  report_selection_string_list = """custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
erp5_corporate_identity_book
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      } 


  contract_selection_string_list = \
"""
custom
erp5_font
erp5_interaction_drop
erp5_web_hal_json
slapos_erp5
slapos_upgrader
%(slapos_folder_list)s
erp5_officejs_codemirror
erp5_officejs_common
erp5_officejs_notebook
erp5_officejs_pdf_viewer
erp5_officejs_svg_editor
erp5_text_editor
erp5_km
erp5_knowledge_pad
erp5_simulation
erp5_dms_base
erp5_dms_web
%(common2_folder_list)s
erp5_corporate_identity_contract
%(common3_folder_list)s
erp5_immobilisation
erp5_ingestion
erp5_integration
erp5_invoicing
%(common_folder_list)s
erp5_xhtml_style
external_method
slapos_disaster_recovery
""" % {'common_folder_list' : common_folder_list,
       'common2_folder_list' : common2_folder_list,
       'common3_folder_list' : common3_folder_list,
       'slapos_folder_list': slapos_folder_list
      } 

  def getTitle(self):
    return "Slapos Skin Selection"

  def test_01_defaultSkin(self):
    """
    Check default skin
    """
    self.assertSameSet(
        self.portal.portal_skins.getDefaultSkin(),
        'View')

  def assertSameSkinSelection(self, skin_name, selection_string_list):
    if selection_string_list.startswith('\n'):
      selection_string_list = selection_string_list[1:]
    if selection_string_list.endswith('\n'):
      selection_string_list = selection_string_list[:-1]

    installed_selection_string_list = \
      self.portal.portal_skins.getSkinPath(skin_name)

    selection_string_list = selection_string_list.split('\n')

    installed_selection_string_list = \
      [ i for i in installed_selection_string_list.split(',')
                             if i not in self.ignore_list]
    if selection_string_list != installed_selection_string_list:
      message = '\nSkin "%s" is different from production server:\n' % skin_name
      for line in difflib.unified_diff(
              selection_string_list,
              installed_selection_string_list
      ):
        message += '\t%s\n' % line

      message += '\n'
      message += 'Removed skin folder:\n'
      for i in [x for x in selection_string_list if x not in
          installed_selection_string_list]:
        message += '\t - %s\n' % i
      message += 'Added skin folder:\n'
      for i in [x for x in installed_selection_string_list if x not in
          selection_string_list]:
        message += '\t + %s\n' % i
      self.fail(message)

  def _test_01_availableSkin(self):
    """
    Check that available skins are the same than production server
    """
    portal = self.getPortal()
    self.assertSameSet(
        [x[0] for x in portal.portal_skins.getSkinPaths()],
        self.expected_available_skin
    )

  def _test_092_RedirectAssist_selection(self):
    self.assertSameSkinSelection('RedirectAssist',
      self.redirect_assistant_selection_string_list)

  def _test_091_Deffered_selection(self):
    self.assertSameSkinSelection('Deferred',
      self.deffered_selection_string_list)

  def _test_09_Deploy_selection(self):
    self.assertSameSkinSelection("Deploy",
      self.deploy_selection_string_list)

  def _test_08_View_selection(self):
    self.assertSameSkinSelection('View',
      self.view_selection_string_list)

  def _test_10_KM_selection(self):
    self.assertSameSkinSelection("KM",
      self.km_selection_string_list)

  def _test_11_Multiflex_selection(self):
    self.assertSameSkinSelection("Multiflex",
      self.multiflex_selection_string_list)

  def _test_12_Download_selection(self):
    self.assertSameSkinSelection("Download",
      self.download_selection_string_list)

  def _test_13_ODS_selection(self):
    self.assertSameSkinSelection("ODS",
      self.ods_selection_string_list)

  def _test_14_ODT_selection(self):
    self.assertSameSkinSelection("ODT",
      self.odt_selection_string_list)

  def _test_15_RSS_selection(self):
    self.assertSameSkinSelection("RSS",
      self.rss_selection_string_list)

  def _test_16_SHACACHE_selection(self):
    self.assertSameSkinSelection("SHACACHE",
      self.shacache_selection_string_list)

  def _test_17_SHADIR_selection(self):
    self.assertSameSkinSelection("SHADIR",
      self.shadir_selection_string_list)

  def _test_18_RJS_selection(self):
    self.assertSameSkinSelection("RJS",
      self.rjs_selection_string_list)

  def _test_19_SlapOSHalRestricted_selection(self):
    self.assertSameSkinSelection("SlapOSHalRestricted",
      self.slapos_hal_restricted_selection_string_list)

  def _test_20_SlideShow_selection(self):
    self.assertSameSkinSelection("SlideShow",
      self.slideshow_selection_string_list)

  def _test_21_AppCache_selection(self):
    self.assertSameSkinSelection("AppCache",
      self.appcache_selection_string_list)

  def _test_22_Leaflet_selection(self):
    self.assertSameSkinSelection("Leaflet",
      self.leaflet_selection_string_list)

  def _test_23_Release_selection(self):
    self.assertSameSkinSelection("Release",
      self.release_selection_string_list)

  def _test_24_Slide_selection(self):
    self.assertSameSkinSelection("Slide",
      self.slide_selection_string_list)

  def _test_25_Book_selection(self):
    self.assertSameSkinSelection("Book",
      self.book_selection_string_list)

  def _test_26_CI_web_selection(self):
    self.assertSameSkinSelection("CI_web",
      self.ci_web_selection_string_list)

  def _test_27_Letter_selection(self):
    self.assertSameSkinSelection("Letter",
      self.letter_selection_string_list)

  def _test_28_Report_selection(self):
    self.assertSameSkinSelection("Report",
      self.report_selection_string_list)

  def _test_29_Contract_selection(self):
    self.assertSameSkinSelection("Contract",
      self.contract_selection_string_list)

class TestSlaposSkinSelection(TestSlaposSkinSelectionMixin):

  test_01_availableSkin = TestSlaposSkinSelectionMixin._test_01_availableSkin
  test_092_RedirectAssist_selection = TestSlaposSkinSelectionMixin._test_092_RedirectAssist_selection
  test_091_Deffered_selection = TestSlaposSkinSelectionMixin._test_091_Deffered_selection
  test_09_Deploy_selection = TestSlaposSkinSelectionMixin._test_09_Deploy_selection
  test_08_View_selection = TestSlaposSkinSelectionMixin._test_08_View_selection
  test_10_KM_selection = TestSlaposSkinSelectionMixin._test_10_KM_selection
  test_11_Multiflex_selection = TestSlaposSkinSelectionMixin._test_11_Multiflex_selection
  test_12_Download_selection = TestSlaposSkinSelectionMixin._test_12_Download_selection
  test_13_ODS_selection = TestSlaposSkinSelectionMixin._test_13_ODS_selection
  test_14_ODT_selection = TestSlaposSkinSelectionMixin._test_14_ODT_selection
  test_15_RSS_selection = TestSlaposSkinSelectionMixin._test_15_RSS_selection
  test_16_SHACACHE_selection = TestSlaposSkinSelectionMixin._test_16_SHACACHE_selection
  test_17_SHADIR_selection = TestSlaposSkinSelectionMixin._test_17_SHADIR_selection
  test_18_RJS_selection = TestSlaposSkinSelectionMixin._test_18_RJS_selection
  test_19_SlapOSHalRestricted_selection = TestSlaposSkinSelectionMixin._test_19_SlapOSHalRestricted_selection
  test_20_SlideShow_selection = TestSlaposSkinSelectionMixin._test_20_SlideShow_selection
  test_21_AppCache_selection = TestSlaposSkinSelectionMixin._test_21_AppCache_selection
  test_22_Leaflet_selection = TestSlaposSkinSelectionMixin._test_22_Leaflet_selection
  test_23_Release_selection = TestSlaposSkinSelectionMixin._test_23_Release_selection
  test_24_Slide_selection = TestSlaposSkinSelectionMixin._test_24_Slide_selection
  test_25_Book_selection = TestSlaposSkinSelectionMixin._test_25_Book_selection
  test_27_Letter_selection = TestSlaposSkinSelectionMixin._test_27_Letter_selection
  test_28_Report_selection = TestSlaposSkinSelectionMixin._test_28_Report_selection
  test_29_Contract_selection = TestSlaposSkinSelectionMixin._test_29_Contract_selection
