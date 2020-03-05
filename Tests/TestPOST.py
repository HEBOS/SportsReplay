import requests
import json

data = {"playgroundId": 1, "plannedStartTime": 1570544400000,
        "camera1Activity": 1570561135781, "camera2Activity": 1570561135747,
        "videoMakerActivity": 1570561136111, "detectorActivity": 1570561124784}
headers = {'content-type': 'application/json'}
result = requests.post(url="http://IP_ADDRESS_OF_YOUR_SERVER:8080/api/recording-heartbeat", data=json.dumps(data), headers=headers)
print(result.text)