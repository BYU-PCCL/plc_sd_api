from ...config import control_net_pipe, NUM_EXCESS_BYTES
from fastapi import APIRouter
from typing import Annotated
import numpy as np
from diffusers.utils import load_image
import base64
from io import BytesIO
from PIL import Image
import numpy as np
from diffusers.utils import load_image
import cv2
from ..data.db import Data

from fastapi import FastAPI, UploadFile, Form

router = APIRouter()
storage = Data.get_storage_instance()

bucket = storage.bucket()

@router.post("/sketch_image/")
async def process_image(username: Annotated[str, Form()], prompt: Annotated[str, Form()], image: Annotated[UploadFile, Form()]):

    orig_sketch_path = f"images/{username}-sketch.png"
    orig_blob = bucket.blob(orig_sketch_path)

    image_data = image.file.read()

    orig_blob.upload_from_string(image_data, content_type="image/png")

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
    image = control_net_pipe(prompt, image, num_inference_steps=20, negative_prompt=negative_prompt).images[0]
    
    image_bytes = BytesIO()
    image.save(image_bytes, format="JPEG")  # You can use JPEG or other formats as needed
    image_bytes = image_bytes.getvalue()

    base64_image = base64.b64encode(image_bytes).decode()

    ai_sketch_path = f"images/{username}-ai-sketch.jpg"
    ai_blob = bucket.blob(ai_sketch_path)

    ai_blob.upload_from_string(image_bytes, content_type="image/jpeg")


    return {"image_base64": base64_image}


@router.get("/get_ai_sketch/{username}")
def get_ai_sketch(username: str):
    file_path = f"images/{username}-ai-sketch.jpg"
    blob = bucket.blob(file_path)

    if blob.exists():
        byte_data = blob.download_as_bytes()

        return base64.b64encode(byte_data)

@router.get("/get_sketch/{username}")
def get_ai_sketch(username: str):
    file_path = f"images/{username}-sketch.png"
    blob = bucket.blob(file_path)

    if blob.exists():
        byte_data = blob.download_as_bytes()

        return base64.b64encode(byte_data)