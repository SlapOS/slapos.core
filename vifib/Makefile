# Vifib
# See LICENSE file for copyright and license details.

NAME = build

TARBALL = vifib.tar.gz

DEVDIR = ${NAME}_dev
RELDIR = ${NAME}

JSDIR = js
DEVJS = vifib.js
DEVCSS = vifib.css
FINALJS = vifib.js
FINALCSS = vifib.css

all: dev release

#########################################
# Dev environment
#########################################

# Emulate server responses with sinonjs
fake: dev ${DEVDIR}/js/fake.js
	cat $(CATJSFILES) ${DEVDIR}/js/fake.js > ${DEVDIR}/$(DEVJS)

${DEVDIR}/js/fake.js: js/utils/fake.js
	@mkdir -p $(@D)
	cp $< $@

# Sort files for concatenation
CATJSFILES = ${DEVDIR}/lib/jquery.js ${DEVDIR}/lib/sinon.js ${DEVDIR}/lib/mustache.js ${DEVDIR}/lib/spin.js ${DEVDIR}/lib/modernizr.js ${DEVDIR}/lib/swipe.js ${DEVDIR}/js/jquery.slapos.js ${DEVDIR}/js/init.js ${DEVDIR}/lib/jquery-mobile.js ${DEVDIR}/js/url.js ${DEVDIR}/js/route.js ${DEVDIR}/js/main.js ${DEVDIR}/js/render.js ${DEVDIR}/js/panels.js ${DEVDIR}/js/pages.js ${DEVDIR}/js/pages.mobile.js ${DEVDIR}/js/pages.tablet.js ${DEVDIR}/js/pages.desktop.js

CATCSSFILES = ${DEVDIR}/lib/qunit.css

# List all javascript files except tests files
JSFILES = $(find $(JSDIR) -name 'tests' -prune -o -name "*.js" -print)

dev: ${DEVDIR}/lib/sinon.js ${DEVDIR}/lib/jquery.js ${DEVDIR}/lib/qunit.js ${DEVDIR}/lib/qunit.css ${DEVDIR}/lib/jquery-mobile.js ${DEVDIR}/lib/modernizr.js ${DEVDIR}/lib/mustache.js ${DEVDIR}/lib/spin.js ${DEVDIR}/lib/swipe.js $(patsubst %.js, ${DEVDIR}/js/%.js, $(JSFILES)) ${DEVDIR}/index.html ${DEVDIR}/$(DEVJS) ${DEVDIR}/$(DEVCSS)

${DEVDIR}/index.html: index.html
	@mkdir -p $(@D)
	cp $< $@

# Lint javascript files #
${DEVDIR}/js/%.js: js/%.js
	@mkdir -p $(@D)
	#${JSLINT} --indent 2 --maxerr 3 $<
	cp $< $@

# Dependencies #
${DEVDIR}/lib/qunit.%:
	@mkdir -p $(@D)
	curl -s -o $@ http://code.jquery.com/qunit/qunit-1.5.0$(suffix $@)

${DEVDIR}/lib/jquery.js:
	@mkdir -p $(@D)
	curl -s -o $@ http://code.jquery.com/jquery-1.7.2.js

${DEVDIR}/lib/sinon.js:
	@mkdir -p $(@D)
	curl -s -o $@ http://sinonjs.org/releases/sinon-1.3.4.js

${DEVDIR}/lib/jquery-mobile.js:
	@mkdir -p $(@D)
	curl -s -o $@ http://code.jquery.com/mobile/1.1.1/jquery.mobile-1.1.1.js

${DEVDIR}/lib/mustache.js:
	@mkdir -p $(@D)
	curl -s -o $@ https://raw.github.com/janl/mustache.js/master/mustache.js

${DEVDIR}/lib/spin.js:
	@mkdir -p $(@D)
	curl -s -o $@ http://fgnass.github.com/spin.js/dist/spin.js

${DEVDIR}/lib/swipe.js:
	@mkdir -p $(@D)
	curl -s -o $@ https://raw.github.com/bradbirdsall/Swipe/master/swipe.js

${DEVDIR}/lib/modernizr.js:
	@mkdir -p $(@D)
	curl -s -o $@ http://modernizr.com/downloads/modernizr-2.5.3.js

# Concatenation #
${DEVDIR}/$(DEVJS): $(CATJSFILES)
	@mkdir -p $(@D)
	cat $^ > $@

${DEVDIR}/$(DEVCSS): $(CATCSSFILES)
	@mkdir -p $(@D)
	cat $^ > $@

#########################################
# Automated test
#########################################
test: dev $(patsubst js/tests/%_test.html, ${DEVDIR}/tests/%_test.html.ok, $(wildcard js/tests/*_test.html))

${DEVDIR}/tests/%_test.html: js/tests/%_test.html
	@mkdir -p $(@D)
	cp $< $@

${DEVDIR}/tests/%_test.js: js/tests/%_test.js
	@mkdir -p $(@D)
	cp $< $@

${DEVDIR}/tests/%_test.html.ok: ${DEVDIR}/tests/%_test.html ${DEVDIR}/tests/%_test.js ${DEVDIR}/js/%.js
	xvfb-run phantomjs js/tests/run-qunit.js $<
	@sleep 1
	touch $@

#########################################
# Release
#########################################

# Sort files for concatenation
#CATFINALJSFILES = ${DEVDIR}/lib/jquery.js ${DEVDIR}/lib/mustache.js ${DEVDIR}/lib/spin.js ${DEVDIR}/lib/modernizr.js ${DEVDIR}/lib/swipe.js ${DEVDIR}/js/jquery.slapos.js ${DEVDIR}/js/init.js ${DEVDIR}/lib/jquery-mobile.js ${DEVDIR}/js/url.js ${DEVDIR}/js/route.js ${DEVDIR}/js/main.js ${DEVDIR}/js/render.js ${DEVDIR}/js/panels.js ${DEVDIR}/js/pages.js ${DEVDIR}/js/pages.mobile.js ${DEVDIR}/js/pages.tablet.js ${DEVDIR}/js/pages.desktop.js

#release: ${DEVDIR}/lib/jquery.js ${DEVDIR}/lib/jquery-mobile.js ${DEVDIR}/lib/modernizr.js ${DEVDIR}/lib/mustache.js ${DEVDIR}/lib/spin.js ${DEVDIR}/lib/swipe.js $(patsubst %.js, ${DEVDIR}/js/%.js, $(JSFILES)) ${DEVDIR}/index.html ${DEVDIR}/$(FINALJS)

 #Concatenation, minification #
#${DEVDIR}/$(FINALJS): $(CATFINALJSFILES)
	#@mkdir -p $(@D)
	#cat $^ | uglifyjs > $@

#tarball: ${DEVDIR}/$(FINALJS) ${DEVDIR}/index.html
	#tar -czf $(TARBALL) $^

#export: tarball

#########################################
# Cleaning
#########################################
clean:
	@echo soft cleaning
	rm -rf ${DEVDIR}/index.html ${DEVDIR}/vifib.* ${DEVDIR}/js
cleanall: 
	@echo cleaning
	rm -rf ${DEVDIR} ${RELDIR} $(TARBALL)
