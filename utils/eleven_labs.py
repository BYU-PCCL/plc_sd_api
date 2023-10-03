import requests
import os

def get_voices():

    headers = {
        "Accept": "application/json",
        "xi-api-key": os.environ["VOICE_API_KEY"]
    }

    voices_url = f'https://api.elevenlabs.io/v1/voices'
    voices_response = requests.get(voices_url, headers=headers)

    for voice in voices_response.json()['voices']:
        print(voice["name"])


get_voices()