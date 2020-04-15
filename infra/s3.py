from troposphere import GetAtt, Join, Ref, Sub, Template
from troposphere.s3 import Bucket, BucketEncryption, ServerSideEncryptionByDefault, ServerSideEncryptionRule, LifecycleConfiguration, LifecycleRule, LifecycleRuleTransition, NoncurrentVersionTransition, PublicAccessBlockConfiguration, BucketPolicy

region = "eu-west-1"
template = Template(
    region + " s3"
)

# TODO seperate out management and log buckets
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

# TODO the account id are hardcoded per region, see: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html
management_bucket_policy = BucketPolicy(
    region.replace("-", "") + "managementbucketpolicy",
    Bucket = Ref(management_bucket),
    PolicyDocument = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::156460612806:root"
                },
                "Action": "s3:PutObject",
                "Resource": Sub("arn:aws:s3:::mgmt.eu-west-1.weblox.io/logs/AWSLogs/${AWS::AccountId}/*"),
            },
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "delivery.logs.amazonaws.com"
                },
                "Action": "s3:PutObject",
                "Resource": Sub("arn:aws:s3:::mgmt.eu-west-1.weblox.io/logs/AWSLogs/${AWS::AccountId}/*"),
                "Condition": {
                    "StringEquals": {
                        "s3:x-amz-acl": "bucket-owner-full-control"
                    }
                }
            },
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "delivery.logs.amazonaws.com"
                },
                "Action": "s3:GetBucketAcl",
                "Resource": "arn:aws:s3:::mgmt.eu-west-1.weblox.io"
            }
        ]
    }   
)

template.add_resource(management_bucket_policy)

print(template.to_yaml())

