import cv2
from PIL import Image
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler
import torch
import numpy as np
from diffusers.utils import load_image

from fastapi import FastAPI, UploadFile, Form
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import requests
import os
from data_model import User
from db import Data
import base64

from io import BytesIO

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-canny", torch_dtype=torch.float16
)

pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", controlnet=controlnet, safety_checker=None, torch_dtype=torch.float16
)

pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

# Remove if you do not have xformers installed
# see https://huggingface.co/docs/diffusers/v0.13.0/en/optimization/xformers#installing-xformers
# for installation instructions
pipe.enable_xformers_memory_efficient_attention()

pipe.enable_model_cpu_offload()


control_net_scribble = ControlNetModel.from_pretrained(
    "lllyasviel/sd-controlnet-scribble", torch_dtype=torch.float16
)

control_net_pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5", controlnet=control_net_scribble, safety_checker=None, torch_dtype=torch.float16
)

control_net_pipe.scheduler = UniPCMultistepScheduler.from_config(control_net_pipe.scheduler.config)
control_net_pipe.enable_xformers_memory_efficient_attention()

control_net_pipe.enable_model_cpu_offload()


@app.post("/process_image/")
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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
