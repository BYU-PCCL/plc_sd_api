from fastapi import APIRouter, UploadFile, Form
from typing import Annotated
from fastapi.responses import StreamingResponse
from ..data.db import Data
from ..data.data_model import User
from .user import has_voice
from plc_sd_api.config import VoicePrompt
import os
import io

import requests

router = APIRouter()

@router.post("/record")
def record(username: Annotated[str, Form()], recording: Annotated[UploadFile, Form()]):
    user = User(username)

    headers = {
        "Accept": "application/json",
        "xi-api-key": os.environ["VOICE_API_KEY"]
    }

    has_voice(username, headers=headers, delete=True)

    try:
        audio_data = recording.file.read()

        storage_filename = f"audio/{recording.filename}"
        storage = Data.get_storage_instance()
        bucket = storage.bucket()
        blob = bucket.blob(storage_filename)
        blob.upload_from_string(audio_data, content_type="audio/wav")

        user["orig_audio_file"] = storage_filename

        url = "https://api.elevenlabs.io/v1/voices/add"

        data = {
            'name': f'{username} voice',
            'labels': '{"accent": "American"}',
        }

        files = [
            ('files', (recording.filename, audio_data, 'audio/wav'))
        ]

        response = requests.post(url, headers=headers, data=data, files=files)

        success = False
        if response.status_code == 200:
            user["ellabs_orig_voice"] = response.json()["voice_id"]
            success = True

        user.save()
        return {"success": success}

    except Exception as e:
        # Log or return the error
        return {"success": False}
    finally:
        recording.file.close()


@router.post("/write_prompt")
def voice_prompt(text_prompt: VoicePrompt):
    storage = Data.get_storage_instance()
    bucket = storage.bucket()

    user = User(text_prompt.username)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{user['ellabs_orig_voice']}"

    headers = {
        "Accept": "application/json",
        "xi-api-key": os.environ["VOICE_API_KEY"]
    }

    body = {
        "text": text_prompt.text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 1,
            "similarity_boost": 1,
            "style": .40,
            "use_speaker_boost": True
        }
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        storage_filename = f"audio/{text_prompt.username}-ai-voice.mp3"
        audio_data = response.content
        destination_blob_name = storage_filename
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_string(audio_data, content_type="audio/mp3")
        user["ellabs_ai_audio_file"] = storage_filename

        # Audio data really just contains the voice_id for the returned recording, put in json
        user.save()

        headers = {
            "Content-Type": "audio/mpeg"
        }

        # encoded_byte_data = base64.b64encode(audio_data).decode('utf-8')
        return StreamingResponse(io.BytesIO(audio_data), headers=headers)

    return AiAudioResponse(content='', success=False)

@router.post("/user_image")
def user_portrait(username: Annotated[str, Form()], image: Annotated[UploadFile, Form()]):
    user = User(username)

    storage = Data.get_storage_instance()
    bucket = storage.bucket()

    storage_filename = f"images/{username}-orig-portrait.jpg"
    image_data = image.file.read()
    blob = bucket.blob(storage_filename)
    blob.upload_from_string(image_data, content_type="image/jpeg")
    user["orig_self_portrait"] = storage_filename
    user.save()

    return

