#!/usr/bin/env python3
"""Validate res/raw/watchface.xml against the official WFF v2 XSD (google/watchface, Apache-2.0).

The official schema uses XSD 1.1 (maxOccurs > 1 inside xs:all) which libxml2 can't parse, so the
schema is loaded from a temp copy where that single constraint is relaxed to "unbounded" via a
sequence-free rewrite (xs:all -> xs:choice maxOccurs=unbounded). Everything else - element
names, nesting, attribute names, enums, types - is checked exactly. This is therefore a slightly
more permissive check than google's own validator; run that too before publishing to Play.
"""
import os, re, shutil, sys, tempfile
from lxml import etree

here = os.path.dirname(os.path.abspath(__file__))
xml = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "app/src/main/res/raw/watchface.xml")

tmp = tempfile.mkdtemp()
try:
    dst = os.path.join(tmp, "s")
    shutil.copytree(os.path.join(here, "wff_schema_v2"), dst)
    for root, _, files in os.walk(dst):
        for f in files:
            if not f.endswith(".xsd"):
                continue
            p = os.path.join(root, f)
            s = open(p, encoding="utf-8").read()
            # xs:all with repeatable children is XSD 1.1 only -> xs:choice (unbounded) is the 1.0 superset
            s = re.sub(r"<xs:all(\s[^>]*)?>", '<xs:choice minOccurs="0" maxOccurs="unbounded">', s)
            s = s.replace("</xs:all>", "</xs:choice>")
            # upstream quirk: hsbFilterElement.xsd includes itself (Xerces tolerates it, libxml2 doesn't)
            s = re.sub(r'<xs:include\s+schemaLocation="%s"\s*/>' % re.escape(f), "", s)
            s = s.replace("\\_", "_")   # libxml2 rejects the escape "\_" in patterns
            open(p, "w", encoding="utf-8").write(s)
    schema = etree.XMLSchema(etree.parse(os.path.join(dst, "watchface.xsd")))
finally:
    shutil.rmtree(tmp, ignore_errors=True)

doc = etree.parse(xml)
if schema.validate(doc):
    print("VALID (relaxed XSD 1.0 check): %s" % os.path.relpath(xml))
else:
    for e in schema.error_log:
        print("line %d: %s" % (e.line, e.message))
    sys.exit(1)
