import torch
from diffusers import StableDiffusionPipeline
import argparse
import os
from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont
import textwrap

def parse_args():
    parser = argparse.ArgumentParser(description='Generate images using Stable Diffusion 3')
    parser.add_argument('--prompt_file', type=str, default='prompts.txt',
                        help='Path to the text file containing prompts')
    parser.add_argument('--output_dir', type=str, default='images',
                        help='Directory to save generated images')
    parser.add_argument('--steps', type=int, default=28,
                        help='Number of inference steps')
    parser.add_argument('--guidance_scale', type=float, default=7.0,
                        help='Guidance scale for generation')
    parser.add_argument('--negative_prompt', type=str, default='ugly,portrait,smooth',
                        help='Negative prompt for generation')
    parser.add_argument('--batch_size', type=int, default=6,
                        help='Number of images to generate in parallel')
    return parser.parse_args()


def setup_pipeline():
    pipe = StableDiffusionPipeline.from_pretrained(
        # "stabilityai/stable-diffusion-3-medium-diffusers",
        "OFA-Sys/small-stable-diffusion-v0",
        torch_dtype=torch.bfloat16
    )
    return pipe.to("cuda")

def read_prompts(prompt_file):
    with open(prompt_file, 'r') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def add_text_to_image(image, prompt):
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Create a new image with extra space for text
    margin = 60
    wrapped_text = textwrap.fill(prompt, width=60)
    text_height = len(wrapped_text.split('\\n')) * 30
    
    new_img = Image.new('RGB', (image.width, image.height + margin + text_height), 'white')
    new_img.paste(image, (0, 0))
    
    # Add text
    draw = ImageDraw.Draw(new_img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
    
    draw.text((10, image.height + margin/2), wrapped_text, 
              font=font, fill='black')
    
    return new_img

def generate_images(pipe, prompts, output_dir, steps, guidance_scale, negative_prompt, batch_size):
    os.makedirs(output_dir, exist_ok=True)
    
    # Process prompts in batches
    for batch_start in tqdm(range(0, len(prompts), batch_size), desc="Processing batches"):
        batch_end = min(batch_start + batch_size, len(prompts))
        batch_prompts = prompts[batch_start:batch_end]
        
        try:
            # Generate images for the batch
            batch_images = pipe(
                batch_prompts,
                negative_prompt=[negative_prompt] * len(batch_prompts),
                num_inference_steps=steps,
                guidance_scale=guidance_scale,
            ).images
            
            # Save each image in the batch
            for idx, (prompt, image) in enumerate(zip(batch_prompts, batch_images)):
                global_idx = batch_start + idx
                
                # Add text to image
                image_with_text = add_text_to_image(image, prompt)
                
                # Save image
                image_path = os.path.join(output_dir, f"generated_{global_idx:03d}.png")
                image_with_text.save(image_path)
                
                # Log the prompt and corresponding filename
                with open(os.path.join(output_dir, "generation_log.txt"), "a") as f:
                    f.write(f"Image {global_idx:03d}: {prompt}\\n")
                
        except Exception as e:
            print(f"Error generating batch starting at index {batch_start}: {e}")
            continue

def main():
    args = parse_args()
    
    # Setup pipeline
    pipe = setup_pipeline()
    
    # Read prompts
    prompts = read_prompts(args.prompt_file)
    
    # Generate images
    generate_images(
        pipe,
        prompts,
        args.output_dir,
        args.steps,
        args.guidance_scale,
        args.negative_prompt,
        args.batch_size
    )

if __name__ == "__main__":
    main()