LDLIBS = -lz
include Makefile.conf

.PHONY: all install uninstall clean

all: check

slapos-core-test: main.c
	$(CC) $(CPPFLAGS) $(CFLAGS) $(LDFLAGS) -o $@ $< $(LDLIBS)

install: all
	install -Dp slapos-core-test $(DESTDIR)$(PREFIX)/bin/slapos-core-test

clean:
	-rm -f slapos-core-test

check: slapos-core-test
	./slapos-core-test

dist: main.c Makefile configure
	tar --transform 's,^,slapos-core-test-0.0.0/,' -czvf dist.tar.gz $?
