import io
import numpy as np
import requests
import json
import os 
import uuid
import boto3
from botocore.client import Config
from prometheus_client import generate_latest
from PIL import Image
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware


# TorchServe API endpoints
TORCHSERVE_MANAGEMENT_API = os.getenv("TORCHSERVE_MANAGEMENT_API",'http://localhost:8081')
TORCHSERVE_INFERENCE_API = os.getenv("TORCHSERVE_INFERENCE_API","http://localhost:8080")


# print(f"{TORCHSERVE_INFERENCE_API=}\n{TORCHSERVE_MANAGEMENT_API=}")
# \n{os.getenv('AWS_ACCESS_KEY_ID')=}\n{os.getenv('AWS_SECRET_ACCESS_KEY')=}

BUCKET_NAME = r"sd3-bucket"
OBEJECTS_PREFIX = "img-output"


# Initialize S3 client

########################################################################################################################################
#   # https://github.com/boto/boto3/issues/3710  
#
#   while trying presigned_url later showing 
#    <Code>SignatureDoesNotMatch</Code>
#    <Message>The request signature we calculated does not match the signature you provided. Check your key and signing method.</Message>
#
########################################################################################################################################

s3_client = boto3.client(
                    's3',
                    config=Config(
                            signature_version="s3v4",
                            region_name="ap-south-1",
                            s3={"addressing_style": "path"}
                    ),
                    region_name="ap-south-1",
                    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)
buckets_response = s3_client.list_buckets()
buckets = list(bucket.get('Name') for bucket in buckets_response['Buckets'])
# print(buckets)
if BUCKET_NAME not in buckets:
    s3_client.create_bucket(Bucket=BUCKET_NAME,CreateBucketConfiguration = { 'LocationConstraint':'ap-south-1'}) # ACL='public-read',
    # client.put_public_access_block( Bucket=BUCKET_NAME, PublicAccessBlockConfiguration={"BlockPublicAcls": False,"IgnorePublicAcls": False,"BlockPublicPolicy": False,"RestrictPublicBuckets": False})
    # client.put_bucket_policy( 
    #                 Bucket='sd3-bucket', 
    #                 Policy= json.dumps({
    #                     "Version": "2024-12-12",  # Ensure this version string is present and correct
    #                     "Statement": [{ "Sid": "PublicReadGetObject", "Effect": "Allow", "Principal": "*", "Action": "s3:GetObject", "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*" } ] 
    #                 })
    #     )




app = FastAPI(title="SD3Deploy", description="Text to Image Service using SD3",version='1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Store results in memory
results_map = {}

# Fill results_map with data in S3
try:
    s3_results = s3_client.list_objects(Bucket=BUCKET_NAME, Prefix=OBEJECTS_PREFIX)
    if "Contents" in s3_results:
        for res in s3_results["Contents"]:
            job_id = res["Key"].split("/")[1]
            results_map[job_id] = {"status": "SUCCESS", "result": res["Key"]}
except Exception as e:
    print(f"Error loading existing S3 results: {e}")

def submit_inference(uid: str, text: str):
    """Submit inference request to torchserve and save to S3"""
    results_map[uid] = {"status": "PENDING"}
    try:
        # Call torchserve endpoint
        response = requests.post(f"{TORCHSERVE_INFERENCE_API}/predictions/sd3", data=text)
        
        if response.status_code != 200:
            raise Exception(f"Torchserve error: {response.text}")
            
        # Construct image from response
        image = Image.fromarray(np.array(json.loads(response.text), dtype="uint8"))
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        
        # Upload to S3
        filename = f"{OBEJECTS_PREFIX}/{uid}/result.jpeg"
        s3_client.upload_fileobj(img_bytes, BUCKET_NAME, filename)
        
        # Store the S3 reference
        results_map[uid] = {
            "status": "SUCCESS",
            "result": filename
        }
        
    except Exception as e:
        print(f"ERROR :: {e}")
        results_map[uid] = {"status": "ERROR", "message": str(e)}

@app.post("/text-to-image")
async def text_to_image(text: str, background_tasks: BackgroundTasks):
    """Endpoint to submit text-to-image generation request"""
    uid = str(uuid.uuid4())
    background_tasks.add_task(submit_inference, uid, text)
    return {
        "job-id": uid,
        "message": "job submitted successfully"
    }

@app.get("/results/{uid}")
async def get_results(uid: str):
    """Get results for a specific job"""
    if uid not in results_map:
        return {"message": f"job-id={uid} is invalid", "status": "ERROR"}

    result = results_map[uid]
    # print(result)
    if result["status"] == "SUCCESS":
        # Generate presigned URL for S3 access
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": result["result"]},
            ExpiresIn=3600 * 24,  # 24 hours
        )
        return {
            "status": "SUCCESS",
            "url": presigned_url
        }
    elif result["status"] == "ERROR":
        return {
            "status": "ERROR",
            "message": result.get("message", "Unknown error occurred")
        }
    else:
        return {
            "status": result["status"],
            "message": "Job is still processing"
        }


@app.get("/get-models")
async def all_models():
    try:
        res = requests.get(f"{TORCHSERVE_MANAGEMENT_API}/models")
        return {
            'status':"ok",
            "all_models":res.json().get("models")

        }
    except Exception as e:
        return {'status':"fails",'error':str(e)}

@app.get("/models/{model_name}")
async def get_model_details(model_name: str):
    try:
        # Fetch specific model details by name (e.g., /models/sd3)
        res = requests.get(f"{TORCHSERVE_MANAGEMENT_API}/models/{model_name}")
        if res.status_code == 200:
            return {
                'status': "ok",
                "model_details": res.json()  # returning the model's details
            }
        else:
            return {'status': "fails", 'error': f"Model {model_name} not found"}
    except Exception as e:
        return {'status': "fails", 'error': str(e)}

@app.get("/model-health")
async def model_health():
    ''' ping model '''
    try:
        res = requests.get(f"{TORCHSERVE_INFERENCE_API}/ping")
        if res.status_code==200:
            return {'status':"healthy","model":'OK'}
    except Exception as e:
        return {"status": "unhealthy", "s3_connection": str(e)}

@app.get("/s3-health")
async def health():
    """Health check endpoint"""
    try:
        # Test S3 connection
        s3_client.list_objects(Bucket=BUCKET_NAME, Prefix=OBEJECTS_PREFIX, MaxKeys=1)
        return {"status": "healthy", "s3_connection": "ok"}
    except Exception as e:
        return {"status": "unhealthy", "s3_connection": str(e)}

@app.get("/")
async def root():
    return {
        "message": "Welcome to SD3 API",
        "endpoints": {
            "POST /text-to-image": "Submit a text-to-image generation request",
            "GET /results/{uid}": "Get results for a specific job",
            "GET /s3-health": "s3 Health check",
            "GET /model-health": "model-health",
            "GET /models/{model_name}":"model details",
            "GET /get-models": 'list model'
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9080) 