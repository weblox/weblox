import boto3, requests


instance_id = requests.get("http://169.254.169.254/latest/meta-data/instance-id").text.strip()
region = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document").json()["region"].strip()

print(instance_id, region)

ec2 = boto3.resource('ec2', region_name=region)
instance = ec2.Instance(instance_id)
for tag in instance.tags:
    print(tag)


config = """ECS_CLUSTER=foo \
ECS_AVAILABLE_LOGGING_DRIVERS=["json-file", "none"] \
ECS_ENABLE_TASK_IAM_ROLE=true \
ECS_ENABLE_TASK_IAM_ROLE_NETWORK_HOST=true \
ECS_IMAGE_PULL_BEHAVIOR=once"""

print(config)