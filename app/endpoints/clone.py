from fastapi import APIRouter, UploadFile, Form
from typing import Annotated
from fastapi.responses import StreamingResponse
from ..data.db import Data
from ..data.data_model import User
from .user import has_voice
from ...config import VoicePrompt, pipe, UserPortrait, BaseData, NUM_EXCESS_BYTES
import base64
import os
import io
from io import BytesIO
from PIL import Image
import cv2
import numpy as np
import requests
import datetime 
import asyncio

router = APIRouter()

storage = Data.get_storage_instance()

bucket = storage.bucket()

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
    
@router.post("/user_image")
def user_portrait(username: Annotated[str, Form()], image: Annotated[UploadFile, Form()]):
    storage_filename = f"images/{username}-orig-portrait.jpg"
    image_data = image.file.read()
    blob = bucket.blob(storage_filename)
    blob.upload_from_string(base64.b64decode(image_data[NUM_EXCESS_BYTES:]), content_type="image/jpeg")


@router.post("/make_ai_portrait")
def get_ai_portrait(text_prompt: VoicePrompt):

    if text_prompt.username != "":
        file_path = f'images/{text_prompt.username}-orig-portrait.jpg'
        blob = bucket.blob(file_path)

        # Download the file as bytes
        file_bytes = blob.download_as_bytes()

        byte_io = io.BytesIO(file_bytes)

        # Open the image using Pillow
        image = Image.open(byte_io)


        negative_prompt = 'low quality, bad quality, sketches'
        image = np.array(image)

        low_threshold = 100
        high_threshold = 200

        image = np.array(image)
        image = cv2.Canny(image, low_threshold, high_threshold)
        image = image[:, :, None]
        image = np.concatenate([image, image, image], axis=2)
        image = Image.fromarray(image)
        controlnet_conditioning_scale = 0.5

        image = pipe(
            prompt, negative_prompt=negative_prompt, image=image, controlnet_conditioning_scale=controlnet_conditioning_scale,
            ).images[0]
        
        image_bytes = BytesIO()
        image.save(image_bytes, format="JPEG")
        image_bytes = image_bytes.getvalue()

        canny_path = f"images/{username}-canny.jpg"
        canny_blob = bucket.blob(canny_path)

        canny_blob.upload_from_string(image_bytes, content_type="image/jpeg")

        base64_image = base64.b64encode(image_bytes).decode()


        return {"image_base64": base64_image}



@router.post("/get_portrait")
def get_portrait(requestObj: UserPortrait):
    if requestObj.portrait_type == "original":
        file_path = f'images/{requestObj.username}-orig-portrait.jpg'
    else:
        file_path = f'images/{requestObj.username}-ai-portrait.jpg'

    blob = bucket.blob(file_path)

    if blob.exists():
        file_bytes = blob.download_as_bytes()

        return base64.b64encode(file_bytes)

def check_video_status(video_id, headers):

    response = requests.get(url=f"https://api.d-id.com/talks/{video_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception("Failed to fetch video status")

@router.post("/generate_video")
async def generate_video(requestObj: UserPortrait):

    user = User(requestObj.username)
    if requestObj.portrait_type == "original":
        image_file_path = f'images/{requestObj.username}-orig-portrait.jpg'
        audio_file_path = f'audio/{requestObj.username}-ai-voice.mp3'
        
    else:
        image_file_path = f'images/{requestObj.username}-ai-portrait.jpg'
        audio_file_path = f'audio/{requestObj.username}-ai-voice.mp3'

    
    image_blob = bucket.blob(image_file_path)
    audio_blob = bucket.blob(audio_file_path)

    image_download_url = image_blob.generate_signed_url(int(datetime.datetime.now().timestamp()) + 3600, method="GET")
    audio_download_url = audio_blob.generate_signed_url(int(datetime.datetime.now().timestamp()) + 3600, method="GET")

    url = "https://api.d-id.com/talks"

    payload = {
        "script": {
            "type": "audio",
            "subtitles": "false",
            "provider": {
                "type": "microsoft",
                "voice_id": "en-US-JennyNeural"
            },
            "ssml": "false",
            "audio_url": audio_download_url
        },
        "config": {
            "fluent": "false",
            "pad_audio": "0.0"
        },
        "source_url": image_download_url,
        "name": f"{requestObj.username}-video"
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f'Basic {os.environ["DID_API_TOKEN"]}'
    }

    if user.get("talk_d_id", None) != None:
        delete_url = f"https://api.d-id.com/talks/{user['talk_d_id']}"

        delete_response = requests.delete(url=delete_url, headers=headers)

        user["talk_d_id"] = None

        if delete_response.status_code != 200:
            raise Exception("FAILED TO DELETE USER VIDEO")
        
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 201:
        raise Exception("Failed to create video " + str(response.status_code))

    video_id = response.json()["id"]
    user["talk_d_id"] = video_id
    user.save()

    while True:
        video_response = check_video_status(video_id, headers)
        status = video_response["status"]
        
        if status == "done":

            headers = {
                "Content-Type": "video/mp4"
            }
            data = requests.get(url=video_response["result_url"]).content
            return StreamingResponse(BytesIO(data), headers=headers)
        elif status == "rejected" or status == "error":
            return
        
        await asyncio.sleep(1)

@router.post("/get_user_video")
def get_user_video(user_data: BaseData):
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": f'Basic {os.environ["DID_API_TOKEN"]}'
    }

    user = User(user_data.username)

    if user.get("talk_d_id", None):
        response = requests.get(url=f"https://api.d-id.com/talks/{user['talk_d_id']}", headers=headers)
        if response.status_code == 200 and response.json()["status"] == "done":
            headers = {
                "Content-Type": "video/mp4"
            }
            data = requests.get(url=response.json()["result_url"]).content
            return StreamingResponse(BytesIO(data), headers=headers)
    
