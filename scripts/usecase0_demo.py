from amarisoft_api import AmarisoftAPI
import json

api = AmarisoftAPI()

api.connect()

response = api.send({
    "message": "ue_get"
})

print(json.dumps(response, indent=4))

api.disconnect()