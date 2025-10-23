DESTDIR = static_panel/external

all: external_lib

clean: 
	@echo cleaning
	rm -rf ${DESTDIR}

external_lib: \
  ${DESTDIR}/rsvp.js \
	${DESTDIR}/renderjs.js \
	${DESTDIR}/jio.js \
	${DESTDIR}/gadget_erp5_nojqm.css \
	${DESTDIR}/font-awesome/font-awesome-webfont.woff2 \
	${DESTDIR}/font-awesome/font-awesome-webfont.woff \
	${DESTDIR}/font-awesome/font-awesome-webfont.ttf \
	${DESTDIR}/rapidspace-Website.Logo \
	${DESTDIR}/gadget_erp5_page_slap_parameter_form.html \
	${DESTDIR}/gadget_erp5_page_slap_parameter_form.js \
	${DESTDIR}/gadget_erp5_page_slap_parameter_form.css \
	${DESTDIR}/json-editor.gadget.html \
	${DESTDIR}/json-editor.gadget.js \
	${DESTDIR}/json-editor.gadget.css \
	${DESTDIR}/ref-parser.js \
	${DESTDIR}/jsoneditor.js \
	${DESTDIR}/gadget_erp5_page_slap_load_schema.html \
	${DESTDIR}/gadget_erp5_page_slap_load_schema.js \
	${DESTDIR}/slapos_load_software_schema.json \
	${DESTDIR}/slapos_load_meta_schema_xml.json \
	${DESTDIR}/slapos_load_meta_schema_json_in_xml.json \
	${DESTDIR}/cfworker-jsonschema-validator.js \
	${DESTDIR}/URI.js \
	${DESTDIR}/vkbeautify.js \
	${DESTDIR}/domsugar.js

${DESTDIR}/%:
	@mkdir -p $(@D)
	curl -s -o $@ https://panel.rapid.space/$*
