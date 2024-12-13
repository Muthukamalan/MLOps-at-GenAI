import torch
from diffusers import StableDiffusionPipeline
from ts.torch_handler.base_handler import BaseHandler
from abc import ABC
import zipfile
from typing import Any
import numpy as np 

class SDHandler(BaseHandler,ABC):
    def __init__(self):
        self.initialized=False
    
    def initialize(self, context:Any):
        """Initialize function loads the model.pt file and initialized the model object.
           First try to load torchscript else load eager mode state_dict based model.

        Args:
            context (context): It is a JSON Object containing information
            pertaining to the model artifacts parameters.

        Raises:
            RuntimeError: Raises the Runtime error when the model.py is missing

        """
        self.manifest = context.manifest
        properties    = context.system_properties
        model_dir     = properties.get("model_dir")
        self.device = torch.device(
            "cuda:" + str(properties.get("gpu_id"))
            if torch.cuda.is_available() and properties.get("gpu_id") is not None
            else "cpu"
        )

        print(f"torch.cuda.is_available() = {torch.cuda.is_available()}")
        print(f'gpu_id = {properties.get("gpu_id")}')
        with zipfile.ZipFile(model_dir + "/sd3-model.zip", "r") as zip_ref:
            zip_ref.extractall(model_dir + "/model")


        self.pipe = StableDiffusionPipeline.from_pretrained(
            model_dir + "/model", 
            torch_dtype=torch.bfloat16  # SD uses bfloat16 instead of float16
        )
        self.pipe = self.pipe.to(self.device)
        self.initialized = True
        print(f"loaded StableDiffusion3 model from {model_dir}/sd3-model.zip")

    def preprocess(self, requests):
        """Basic text preprocessing, of the user's prompt.
        Args:
            requests (str): The Input data in the form of text is passed on to the preprocess
            function.
        Returns:
            list : The preprocess function returns a list of prompts.
        """
        inputs = []
        for _, data in enumerate(requests):
            input_text = data.get("data")
            if input_text is None:
                input_text = data.get("body")
            if isinstance(input_text, (bytes, bytearray)):
                input_text = input_text.decode("utf-8")
            print("received text: '%s'", input_text)
            inputs.append(input_text)
        return inputs
    

    def inference(self, inputs):
        """Generates the image relevant to the received text.
        Args:
            input_batch (list): List of Text from the pre-process function is passed here
        Returns:
            list : It returns a list of the generate images for the input text
        """
        # SD3 default settings
        inferences = self.pipe(
            inputs,
            num_inference_steps=28,  # SD3 default
            guidance_scale=7.0,      # SD3 default
            width=1024,
            height=1024
        ).images

        print(f"generated images: {inferences}")
        return inferences
    
    def postprocess(self, inference_output):
        """Post Process Function converts the generated image into Torchserve readable format.
        Args:
            inference_output (list): It contains the generated image of the input text.
        Returns:
            (list): Returns a list of the images.
        """
        images = []
        for image in inference_output:
            images.append(np.array(image).tolist())
        return images 