# Makefile for debian packaging

VERSION = $(shell ./pgloader.py --version |cut -d' ' -f3)
PKGVERS = $(shell dpkg-parsechangelog | awk -F '[:-]' '/^Version:/ { print substr($$2, 2) }')

# debian setting
DESTDIR =
DOCS    = getddl.1.txt
SQL     = $(wildcard sql/*.sql)

${DOCS:.txt=.xml}: $(DOCS)
	asciidoc -d manpage -b docbook $<

man: ${DOCS:.txt=.xml}
	xmlto man $<

html: $(DOCS)
	asciidoc -a toc $<

clean:
	rm -f *.xml *.html *.1 *~

install: man
	install -m 755 getddl.py $(DESTDIR)/usr/bin/getddl
	install -m 755 -d $(DESTDIR)/usr/share/getddl/sql
	install -m 644 -t $(DESTDIR)/usr/share/getddl/sql $(SQL)

orig:
	cd .. && tar czf getddl_$(PKGVERS).orig.tar.gz --exclude-vcs getddl

deb: orig
	debuild -us -uc

.PHONY: orig deb
