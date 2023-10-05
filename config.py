from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler
import torch

from pydantic import BaseModel

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

NUM_EXCESS_BYTES = 23
NUM_INFERENCE_STEPS = 20


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
