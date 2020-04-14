from troposphere import Template
from troposphere.s3 import Bucket, BucketEncryption, ServerSideEncryptionByDefault, ServerSideEncryptionRule, LifecycleConfiguration, LifecycleRule, LifecycleRuleTransition, NoncurrentVersionTransition, PublicAccessBlockConfiguration, BucketPolicy

region = "eu-west-1"
template = Template(
    region + " s3"
)

management_bucket = Bucket(
    region.replace("-", "") + "managementbucket",
    BucketName = "mgmt.eu-west-1.weblox.io",
    BucketEncryption = BucketEncryption(
        ServerSideEncryptionConfiguration = [
            ServerSideEncryptionRule(
                ServerSideEncryptionByDefault = ServerSideEncryptionByDefault(
                    SSEAlgorithm = "AES256"
                )
            ),
        ]
    ),
    LifecycleConfiguration = LifecycleConfiguration(
        Rules = [
            LifecycleRule(
                Id="ExpireLogs",
                Prefix="logs/",
                Status="Enabled",
                ExpirationInDays=30,
            ),
        ]
    ),
    PublicAccessBlockConfiguration = PublicAccessBlockConfiguration(
        BlockPublicAcls = True,
        BlockPublicPolicy = True,
        IgnorePublicAcls = True,
        RestrictPublicBuckets = True
    )
)

template.add_resource(management_bucket)

# management_bucket_policy = BucketPolicy(
#     region.replace("-", "") + "managementbucket",   
# )

print(template.to_yaml())

