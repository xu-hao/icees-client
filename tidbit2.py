import icees.iceesclient as ic
import json
import sys
import requests
import numpy as np

# import logging
# # These two lines enable debugging at httplib level (requests->urllib3->http.client)
# # You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# # The only thing missing will be the response.body which is not logged.
# try:
#     import http.client as http_client
# except ImportError:
#     # Python 2
#     import httplib as http_client
# http_client.HTTPConnection.debuglevel = 1

# # You must initialize logging, otherwise you'll not see debug output.
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True

f = sys.argv[1]

data = {
    "natural_question": f"WF5: ({f}) to gene to biological process phenotype association.",
  "machine_question": {
    "nodes": [
      {
        "id": "n0",
        "type": "chemical_substance",
        "curie": [
          f
        ]
      },
      {
        "id": "n1",
        "type": "gene"
      },
      {
        "id": "n2",
        "type": "biological_process_or_activity",
	"set": True
      },
      {
        "id": "n3",
        "type": "phenotypic_feature"
      }
    ],
    "edges": [
      {
        "id": "e0",
        "source_id": "n0",
        "target_id": "n1"
      },
      {
        "id": "e1",
        "source_id": "n1",
        "target_id": "n2"
      },
      {
        "id": "e2",
        "source_id": "n2",
        "target_id": "n3"
      }
    ]
  }
}

res = requests.post("http://robokop.renci.org/api/simple/quick/", params={
    "rebuild":"false",
    "output_format":"MESSAGE",
    "max_connectivity":"0",
    "max_results":250
}, data=json.dumps(data), headers={
    "accept": "application/json",
    "Content-Type": "application/json"
})

print(json.dumps(res.json(), indent="    "))
