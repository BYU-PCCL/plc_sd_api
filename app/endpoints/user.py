from fastapi import APIRouter, UploadFile, Form
import requests
from typing import Annotated
from diffusers.utils import load_image
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import cv2
from ...config import BaseData, pipe
from ..data.data_model import User
from ..data.db import Data
import os
import base64

router = APIRouter()

storage = Data.get_storage_instance()

bucket = storage.bucket()

def has_voice(username: str, headers, delete: bool=False):
    voices_url = f'https://api.elevenlabs.io/v1/voices'
    voices_response = requests.get(voices_url, headers=headers)

    # This snippet checks to see if this person already has a voice and removes
    # that old voice upon recording their new voice.

    if voices_response.ok:
        for voice in voices_response.json()["voices"]:
            if voice["name"] == f'{username} voice':
                print("FOUND VOICE")
                if delete:
                    delete_voice_url = f'https://api.elevenlabs.io/v1/voices/{voice["voice_id"]}'
                    requests.delete(delete_voice_url, headers=headers)
                return True
    return False

@router.get("/has_prompt/{username}")
def has_prompt(username: str):
    if username != "":
        file_path = f'audio/{username}-ai-voice.mp3'
        blob = bucket.blob(file_path)

        if blob.exists():
            return {"success": True}
        return {"success": False}

@router.post("/get_orig_portrait")
def get_orig_portrait(user: BaseData):

    if user.username != "":
        file_path = f'images/{user.username}-orig-portrait.jpg'
        blob = bucket.blob(file_path)

        # Download the file as bytes
        if blob.exists():
            file_bytes = blob.download_as_bytes()

            return base64.b64encode(file_bytes)
    
@router.post("/get_ai_portrait")
def get_orig_portrait(user: BaseData):
    if user.username != "":
        file_path = f'images/{user.username}-ai-portrait.jpg'
        blob = bucket.blob(file_path)

        # Download the file as bytes
        if blob.exists():
            file_bytes = blob.download_as_bytes()

            return base64.b64encode(file_bytes)


@router.post("/signup")
def login(user: BaseData):
    if user.username == "":
        return {"success": False, "message": "Error: Username field was empty"}
    
    db = Data.get_db_instance()

    users_ref = db.reference('/users')

    users = users_ref.get()

    for usr in users.items():
        if usr[1]["user_id"] == user.username:
            return { "success": False, "message": "User Already exists, try logging in instead"}
    
    new_user = User(user.username)
    new_user.initialize()
    new_user.save()

    return {"success": True}


@router.post("/login")
def login(user: BaseData):
    if user.username == "":
        return {"success": False, "message": "Error: Username field was empty"}
    
    db = Data.get_db_instance()

    users_ref = db.reference('/users')

    users = users_ref.get()

    for usr in users.items():
        if usr[1]["user_id"] == user.username:
            return { "success": True }
    
    return { "success": False, "message": "It looks like you don't have an account yet, go ahead and sign up"}

    

@router.get("/has_voice/{username}")
def check_has_recording(username: str):

    headers = {
        "Accept": "application/json",
        "xi-api-key": os.environ["VOICE_API_KEY"]
    }

    return has_voice(username, headers)

@router.post("/generate_canny")
def check_has_recording(username: Annotated[str, Form()], prompt: Annotated[str, Form()], image: Annotated[UploadFile, Form()]):

    file_path = f'images/{username}-canny.jpeg'

    image_data = image.file.read()

    image_stream = BytesIO(image_data)

    image = Image.open(image_stream)

    negative_prompt = 'low quality, bad quality, sketches'
    image = np.array(image)

    low_threshold = 100
    high_threshold = 200

    image = cv2.Canny(image, low_threshold, high_threshold)
    image = image[:, :, None]
    image = np.concatenate([image, image, image], axis=2)
    image = Image.fromarray(image)
    image = pipe(prompt, image, num_inference_steps=20, negative_prompt=negative_prompt).images[0]
    
    image_bytes = BytesIO()
    image.save(image_bytes, format="JPEG")  # You can use JPEG or other formats as needed
    image_bytes = image_bytes.getvalue()

    canny_path = f"images/{username}-canny.jpg"
    canny_blob = bucket.blob(canny_path)

    canny_blob.upload_from_string(image_bytes, content_type="image/jpeg")

    base64_image = base64.b64encode(image_bytes).decode()


    return {"image_base64": base64_image}

@router.get("/get_canny/{username}")
def get_canny(username: str):
    if username != "":

        file_path = f'images/{username}-canny.jpg'
        blob = bucket.blob(file_path)

        if blob.exists():
            file_bytes = blob.download_as_bytes()

            return base64.b64encode(file_bytes)

