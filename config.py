from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler, StableDiffusionXLControlNetPipeline, AutoencoderKL
import torch

from pydantic import BaseModel

controlnet_conditioning_scale = 0.5  # recommended for good generalization

controlnet = ControlNetModel.from_pretrained(
    "diffusers/controlnet-canny-sdxl-1.0",
    torch_dtype=torch.float16
)
vae = AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16)

pipe = StableDiffusionXLControlNetPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    controlnet=controlnet,
    vae=vae,
    torch_dtype=torch.float16,
)

pipe.enable_xformers_memory_efficient_attention()
pipe.enable_model_cpu_offload()

NUM_EXCESS_BYTES = 23
# pipe = control_net_pipe = ""


class BaseData(BaseModel):
    username: str


class ImageReq(BaseData):
    prompt: str


class VoicePrompt(BaseData):
    text: str


class AiAudioResponse(BaseModel):
    content: str
    success: bool

class UserPortrait(BaseData):
    portrait_type: str