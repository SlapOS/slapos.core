# Vifib
# See LICENSE file for copyright and license details.

NAME = build

TARBALL = slapos.tar.gz

JSLINT = jslint
JSLINTOPTIONS = --maxerr=5

DEVDIR = ${NAME}_dev
APPDIR = $(DEVDIR)/app
RELDIR = ${NAME}

JSDIR = js
DEVJS = slapos.js
DEVCSS = slapos.css
FINALJS = slapos.js
FINALCSS = slapos.css

MANIFESTNAME = $(APPDIR)/slapos.manifest

all: test

#########################################
# Dev environment
#########################################

# Emulate server responses with sinonjs
fake: dev $(DEVDIR)/js/fake.js
	more $(DEVDIR)/js/fake.js >> $(APPDIR)/$(DEVJS)
	echo "http://www.system-linux.eu/public/images/kvm-logo.png" >> $(MANIFESTNAME)
	echo "http://www.linux-kvm.org/wiki/skins/kvm/kvmbanner-logo2.png" >> $(MANIFESTNAME)
	echo "http://www.w3.org/html/logo/downloads/HTML5_Badge_512.png" >> $(MANIFESTNAME)
	echo "http://7.mshcdn.com/wp-content/uploads/2011/01/html5-logo-1.jpg" >> $(MANIFESTNAME)

$(DEVDIR)/js/fake.js: js/utils/fake.js
	@mkdir -p $(@D)
	cp $< $@

# Sort files for concatenation
CATJSFILES = $(DEVDIR)/lib/jquery.js $(DEVDIR)/lib/sinon.js $(DEVDIR)/lib/mustache.js $(DEVDIR)/lib/spin.js $(DEVDIR)/lib/modernizr.js $(DEVDIR)/lib/swipe.js $(DEVDIR)/js/jquery.slapos.js $(DEVDIR)/js/init.js $(DEVDIR)/lib/jquery.mobile.js $(DEVDIR)/lib/url.js $(DEVDIR)/lib/route.js $(DEVDIR)/js/main.js $(DEVDIR)/js/render.js $(DEVDIR)/js/panels.js $(DEVDIR)/js/pages.js $(DEVDIR)/js/pages/library.js $(DEVDIR)/js/pages/overview.js $(DEVDIR)/js/pages/dashboard.js $(DEVDIR)/js/pages/login.js

CATCSSFILES = $(DEVDIR)/lib/qunit.css $(DEVDIR)/lib/jquery.mobile.css

# List all javascript files except tests files and lib files
JSFILES = $(find $(JSDIR) -name 'tests' -prune -o -name 'lib' -prune -o -name '*.js' -printf '%p ')

dev: $(DEVDIR)/lib/sinon.js $(DEVDIR)/lib/jquery.js $(DEVDIR)/lib/qunit.js $(DEVDIR)/lib/qunit.css $(DEVDIR)/lib/jquery.mobile.js $(DEVDIR)/lib/jquery.mobile.css $(DEVDIR)/lib/jquery.mobile.zip $(DEVDIR)/lib/modernizr.js $(DEVDIR)/lib/mustache.js $(DEVDIR)/lib/spin.js $(DEVDIR)/lib/swipe.js $(DEVDIR)/lib/route.js $(DEVDIR)/lib/url.js $(subst $(JSDIR)/, $(DEVDIR)/, $(JSFILES)) $(APPDIR)/index.html $(APPDIR)/$(DEVJS) $(APPDIR)/$(DEVCSS) manifest

manifest: $(APPDIR)/index.html $(APPDIR)/$(DEVJS) $(APPDIR)/$(DEVCSS)
	@if test -f $(MANIFESTNAME); then \
		./inc_manifest_release.sh $(MANIFESTNAME); \
	else \
		echo "CACHE MANIFEST" > $(MANIFESTNAME); \
		echo "#rel 1" >> $(MANIFESTNAME); \
		find $(APPDIR) -type f -not -wholename $(MANIFESTNAME) | sed -e 's#$(APPDIR)/##g' >> $(MANIFESTNAME); \
	fi

$(APPDIR)/index.html: index.html
	@mkdir -p $(@D)
	cp $< $@

$(DEVDIR)/js/%.js: js/%.js
	@mkdir -p $(@D)
	@# Prepend jslintrc to defined global variables #
	@more jslintrc | cat - $< > /tmp/$(notdir $<)
	${JSLINT} ${JSLINTOPTIONS} /tmp/$(notdir $<)
	cp $< $@

# Dependencies #
$(DEVDIR)/lib/route.js:
	cp js/lib/route.js $@

$(DEVDIR)/lib/url.js:
	cp js/lib/url.js $@

$(DEVDIR)/lib/qunit.%:
	@mkdir -p $(@D)
	curl -s -o $@ http://code.jquery.com/qunit/qunit-1.5.0$(suffix $@)

$(DEVDIR)/lib/jquery.js:
	@mkdir -p $(@D)
	curl -s -o $@ http://code.jquery.com/jquery-1.7.2.js

$(DEVDIR)/lib/sinon.js:
	@mkdir -p $(@D)
	curl -s -o $@ http://sinonjs.org/releases/sinon-1.3.4.js

$(DEVDIR)/lib/jquery.mobile.js:
	@mkdir -p $(@D)
	curl -s -o $@ http://code.jquery.com/mobile/1.1.1/jquery.mobile-1.1.1.js

$(DEVDIR)/lib/jquery.mobile.css:
	@mkdir -p $(@D)
	curl -s -o $@ http://code.jquery.com/mobile/1.1.0/jquery.mobile-1.1.0.css

$(DEVDIR)/lib/jquery.mobile.zip:
	@mkdir -p $(@D)
	@mkdir -p $(APPDIR)
	curl -s -o $@ http://code.jquery.com/mobile/1.1.0/jquery.mobile-1.1.0.zip
	unzip $@ -d $(DEVDIR) 'jquery.mobile-?.?.?/images/*'
	cp -r $(DEVDIR)/jquery.mobile-1.1.0/images $(APPDIR)/
	rm -rf $(DEVDIR)/jquery.mobile-1.1.0

$(DEVDIR)/lib/mustache.js:
	@mkdir -p $(@D)
	curl -s -o $@ https://raw.github.com/janl/mustache.js/master/mustache.js

$(DEVDIR)/lib/spin.js:
	@mkdir -p $(@D)
	curl -s -o $@ http://fgnass.github.com/spin.js/dist/spin.js

$(DEVDIR)/lib/swipe.js:
	@mkdir -p $(@D)
	curl -s -o $@ https://raw.github.com/bradbirdsall/Swipe/master/swipe.js

$(DEVDIR)/lib/modernizr.js:
	@mkdir -p $(@D)
	curl -s -o $@ http://modernizr.com/downloads/modernizr-2.5.3.js

# Concatenation #
$(APPDIR)/$(DEVJS): $(CATJSFILES)
	@mkdir -p $(@D)
	cat $^ > $@

$(APPDIR)/$(DEVCSS): $(CATCSSFILES)
	@mkdir -p $(@D)
	cat $^ > $@

#########################################
# Automated test
#########################################
test: dev $(patsubst js/tests/%_test.html, $(DEVDIR)/tests/%_test.html.ok, $(wildcard js/tests/*_test.html))

$(DEVDIR)/tests/%_test.html: js/tests/%_test.html
	@mkdir -p $(@D)
	cp $< $@

$(DEVDIR)/tests/%_test.js: js/tests/%_test.js
	@mkdir -p $(@D)
	cp $< $@

$(DEVDIR)/tests/%_test.html.ok: $(DEVDIR)/tests/%_test.html $(DEVDIR)/tests/%_test.js $(DEVDIR)/js/%.js
	xvfb-run phantomjs js/tests/run-qunit.js $<
	@sleep 1
	touch $@

#########################################
# Release
#########################################

# Sort files for concatenation
#CATFINALJSFILES = $(DEVDIR)/lib/jquery.js $(DEVDIR)/lib/mustache.js $(DEVDIR)/lib/spin.js $(DEVDIR)/lib/modernizr.js $(DEVDIR)/lib/swipe.js $(DEVDIR)/js/jquery.slapos.js $(DEVDIR)/js/init.js $(DEVDIR)/lib/jquery-mobile.js $(DEVDIR)/js/url.js $(DEVDIR)/js/route.js $(DEVDIR)/js/main.js $(DEVDIR)/js/render.js $(DEVDIR)/js/panels.js $(DEVDIR)/js/pages.js $(DEVDIR)/js/pages.mobile.js $(DEVDIR)/js/pages.tablet.js $(DEVDIR)/js/pages.desktop.js

#release: $(DEVDIR)/lib/jquery.js $(DEVDIR)/lib/jquery-mobile.js $(DEVDIR)/lib/modernizr.js $(DEVDIR)/lib/mustache.js $(DEVDIR)/lib/spin.js $(DEVDIR)/lib/swipe.js $(patsubst %.js, $(DEVDIR)/js/%.js, $(JSFILES)) $(DEVDIR)/index.html $(DEVDIR)/$(FINALJS)

 #Concatenation, minification #
#$(DEVDIR)/$(FINALJS): $(CATFINALJSFILES)
	#@mkdir -p $(@D)
	#cat $^ | uglifyjs > $@

#tarball: $(DEVDIR)/$(FINALJS) $(DEVDIR)/index.html
	#tar -czf $(TARBALL) $^

#export: tarball

#########################################
# Cleaning
#########################################
clean:
	@echo soft cleaning
	rm -rf $(APPDIR)/*.*
cleanall: 
	@echo cleaning
	rm -rf $(DEVDIR) ${RELDIR} $(TARBALL)
