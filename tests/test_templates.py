import json
import re

import build


def json_ld(html):
    block = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    return block.group(1)


def test_json_ld_survives_quotes_and_markup_in_the_summary(cv):
    summary = 'Experta en "datos" y rutas C:\\temp &lt;/script&gt;&lt;script&gt;alert(1)&lt;/script&gt; con <strong>Python</strong>.'
    html = build.render_cv({**cv, "profile": {"es": summary}}, "es", "")
    data = json.loads(json_ld(html))                      # still one valid JSON document
    assert data["description"].startswith('Experta en "datos" y rutas C:\\temp </script>')
    assert "alert(1)</script>" not in json_ld(html)       # nothing closes the block early


def test_json_ld_keeps_accents_readable(cv):
    html = build.render_cv({**cv, "profile": {"es": "Ingeniería de datos y diseño."}}, "es", "")
    assert "Ingeniería de datos y diseño." in json_ld(html)
