from fastapi import APIRouter
import requests

from plc_sd_api.config import BaseData
from ..data.data_model import User
import os

router = APIRouter()

def has_voice(username: str, headers, delete: bool=False):
    voices_url = f'https://api.elevenlabs.io/v1/voices'
    voices_response = requests.get(voices_url, headers=headers)

    # This snippet checks to see if this person already has a voice and removes
    # that old voice upon recording their new voice.

    if voices_response.ok:
        for voice in voices_response.json()["voices"]:
            if voice["name"] == f'{username} voice':
                if delete:
                    delete_voice_url = f'https://api.elevenlabs.io/v1/voices/{voice["voice_id"]}'
                    requests.delete(delete_voice_url, headers=headers)
                return True
    return False

@router.post("/login")
def login(user: BaseData):
    if user.username == "":
        return {"success": False, "message": "Error: Username field was empty"}
    new_user = User(user.username)
    new_user.initialize()
    new_user.save()

@router.get("/has_voice/{username}")
def check_has_recording(username: str):

    headers = {
        "Accept": "application/json",
        "xi-api-key": os.environ["VOICE_API_KEY"]
    }

    return has_voice(username, headers)