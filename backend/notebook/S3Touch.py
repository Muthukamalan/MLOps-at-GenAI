import boto3
import json 

########################################################################
#
#    Testing Purpose🕵️
#
########################################################################

ACCESS_KEY= r""
SECRET_KEY = r""
BUCKET_NAME = r"sd3-bucket"


client = boto3.client('s3',region_name="ap-south-1",aws_access_key_id= ACCESS_KEY,aws_secret_access_key  =SECRET_KEY)
print(client)
print(client.list_buckets())


# create
client.create_bucket(
            Bucket=BUCKET_NAME,
            CreateBucketConfiguration = { 
                'LocationConstraint':'ap-south-1',
            }) # ACL='public-read',

# access
client.put_public_access_block(
    Bucket=BUCKET_NAME,
    PublicAccessBlockConfiguration={
        "BlockPublicAcls": False,
        "IgnorePublicAcls": False,
        "BlockPublicPolicy": False,
        "RestrictPublicBuckets": False
    }
)

# policy 
client.put_bucket_policy(
    Bucket='sd3-bucket',
    Policy= json.dumps({
                        "Version": "2012-10-17",  # Ensure this version string is present and correct
                        "Statement": [
                            {
                                "Sid": "PublicReadGetObject",
                                "Effect": "Allow",
                                "Principal": "*",
                                "Action": "s3:GetObject",
                                "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*"
                            }
                        ]
                    })
)


# Upload
client.upload_file(Filename='prompts.txt',Bucket=BUCKET_NAME ,Key='hello.txt')