"""Manual live check of MCC database endpoints; no database files are downloaded.

Run: python -m unittest discover -s tests -p 'test_database_links.py' -v
Requires network access. Failures report HTTP, authentication, or connection issues;
HTTP success alone does not validate file contents or response schemas.
"""

import unittest

import requests


# Match the URLs used in MCC/DataCollection/Requests. Representative IDs exercise
# templated URLs; this checks availability, not every model/metabolite entry.
ENDPOINTS = {
    "MetaNetX xref": "https://www.metanetx.org/ftp/latest/chem_xref.tsv",
    "MetaNetX deprecated IDs": "https://www.metanetx.org/ftp/latest/chem_depr.tsv",
    "MetaNetX properties": "https://www.metanetx.org/ftp/latest/chem_prop.tsv",
    "ModelSEED compound index": "https://api.github.com/repos/ModelSEED/ModelSEEDDatabase/contents/Biochemistry",
    "ModelSEED compound download": "https://raw.githubusercontent.com/ModelSEED/ModelSEEDDatabase/master/Biochemistry/compound_00.tsv",
    "BiGG model index": "http://bigg.ucsd.edu/api/v2/models",
    "BiGG model download": "http://bigg.ucsd.edu/static/models/e_coli_core.xml",
    "BiGG metabolite lookup": "http://bigg.ucsd.edu/api/v2/universal/metabolites/glc__D",
    "BioCyc compound lookup": "https://websvc.biocyc.org/getxml?META:GLC&detail=low",
    "BioCyc translation": "https://biocyc.org/META/metabolite-translation-service?=file",
}


class DatabaseLinkTests(unittest.TestCase):
    def test_database_links(self):
        for name, url in ENDPOINTS.items():
            with self.subTest(database=name, url=url):
                try:
                    # Streaming closes the connection after headers, avoiding
                    # downloading the large MetaNetX tables just for this check.
                    options = {"timeout": (5, 10), "stream": True}
                    if name == "BioCyc translation":
                        response = requests.post(url, files={"file": "glucose"}, **options)
                    else:
                        response = requests.get(url, **options)
                    with response:
                        print(f"{name}: HTTP {response.status_code} ({response.url})", flush=True)
                        self.assertEqual(response.status_code, 200,
                                         f"{name}: HTTP {response.status_code} at {response.url}")
                except requests.RequestException as error:
                    self.fail(f"{name}: {error}")


if __name__ == "__main__":
    unittest.main()
