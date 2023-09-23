from plc_sd_api.config import control_net_pipe
from fastapi import APIRouter
from typing import Annotated
import numpy as np
from diffusers.utils import load_image
import os
import base64
from io import BytesIO
from PIL import Image
import numpy as np
from diffusers.utils import load_image
import cv2

from fastapi import FastAPI, UploadFile, Form

router = APIRouter()

@router.post("/process_image/")
async def process_image(image: Annotated[UploadFile, Form()]):

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
    image = control_net_pipe("hyper realistic image of a black cat with a white spot taken with a Nikon camera",image, num_inference_steps=20, negative_prompt=negative_prompt).images[0]
    
    image_bytes = BytesIO()
    image.save(image_bytes, format="JPEG")  # You can use JPEG or other formats as needed
    image_bytes = image_bytes.getvalue()

    base64_image = base64.b64encode(image_bytes).decode()

    return {"image_base64": base64_image}