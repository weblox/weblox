import requests

from troposphere import Base64, GetAtt, Ref, Join, Template
# from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration
# from troposphere.ec2 import LaunchTemplate
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration, LaunchTemplateSpecification, Metadata
from troposphere.ec2 import EBSBlockDevice, LaunchTemplate, LaunchTemplateCreditSpecification, LaunchTemplateBlockDeviceMapping, LaunchTemplateData, IamInstanceProfile
from troposphere.ecs import Cluster, ClusterSetting
from troposphere.ec2 import SecurityGroup, SecurityGroupIngress, SecurityGroupRule
from troposphere.iam import Role, Policy, InstanceProfile
from troposphere.cloudformation import Init, InitConfig, InitFiles, InitFile
from troposphere.cloudformation import InitServices, InitService
from troposphere.ec2 import CreditSpecification

from troposphere.elasticloadbalancingv2 import LoadBalancer, LoadBalancerAttributes, Listener, TargetGroup

image_id = "ami-09cec0d91e6d220ea"
vpc_id = "vpc-0e2786487ff4f2ef4"
region = "eu-west-1"

management_ip = requests.get("https://ipv4.icanhazip.com/").text.strip()

template = Template()
template.set_version("2010-09-09")

security_group = SecurityGroup(
    region.replace("-", "") + "ecslivesg",
    GroupDescription = "Security Group for ECS Live Cluster",
    VpcId = vpc_id
)

security_group_ingress_management = SecurityGroupIngress(
    region.replace("-", "") + "ecslivesgingressmanagement",
    GroupId = GetAtt(security_group, "GroupId"),
    CidrIp = management_ip + "/32",
    IpProtocol = "-1"
)

security_group_ingress_cluster = SecurityGroupIngress(
    region.replace("-", "") + "ecslivesgingresscluster",
    GroupId = GetAtt(security_group, "GroupId"),
    SourceSecurityGroupId = GetAtt(security_group, "GroupId"),
    IpProtocol = "-1"
)

template.add_resource(security_group)
template.add_resource(security_group_ingress_cluster)
template.add_resource(security_group_ingress_management)

cluster = Cluster(
    region.replace("-", "") + "ecslive",
    ClusterName = "live",
    ClusterSettings = [
        ClusterSetting(
            Name = "containerInsights",
            Value = "enabled"
        )
    ]
)

ecs_role = Role(
    region.replace("-", "") + "ecsrole",
    AssumeRolePolicyDocument = {
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            }
        }]    
    },
    ManagedPolicyArns = [
        "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
        "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
    ],
    Policies = [
        Policy(
            PolicyName = "ecs-service",
            PolicyDocument = {
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "ec2:DescribeInstances",
                        "ecs:CreateCluster",
                        "ecs:DeregisterContainerInstance",
                        "ecs:DiscoverPollEndpoint",
                        "ecs:Poll",
                        "ecs:RegisterContainerInstance",
                        "ecs:StartTelemetrySession",
                        "ecs:Submit*",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:BatchGetImage",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:GetAuthorizationToken",
                        "s3:ListAllMyBuckets"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:ListBucket*",
                        "s3:ListObjects*",
                        "s3:GetBucketLocation",
                        "s3:GetObject*"
                    ],
                    "Resource": [
                        "arn:aws:s3:::mgmt.eu-west-1.weblox.io",
                        "arn:aws:s3:::mgmt.eu-west-1.weblox.io/*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": "s3:PutObject*",
                    "Resource": [
                        "arn:aws:s3:::mgmt.eu-west-1.weblox.io/logs",
                        "arn:aws:s3:::mgmt.eu-west-1.weblox.io/logs/*"
                    ]
                },
                {
                    "Effect": "Deny",
                    "Action": "s3:GetObject*",
                    "Resource": [
                        "arn:aws:s3:::mgmt.eu-west-1.weblox.io/logs",
                        "arn:aws:s3:::mgmt.eu-west-1.weblox.io/logs/*"
                    ]
                }]
            }
        )
    ]
)


template.add_resource(ecs_role)

ecs_instance_profile = InstanceProfile(
    region.replace("-", "") + "ecsinstanceprofile",
    Path = "/",
    Roles = [
        Ref(ecs_role)
    ]
)

template.add_resource(ecs_instance_profile)


launch_template = LaunchTemplate(
    region.replace("-", "") + "ecslivelaunchtemplate",
    LaunchTemplateName = "ecs-live-launch-template",
    LaunchTemplateData = LaunchTemplateData(
        ImageId = image_id,
        BlockDeviceMappings = [
            LaunchTemplateBlockDeviceMapping(
                DeviceName = "/dev/xvda",
                Ebs = EBSBlockDevice(
                    "ecsliveblockdevice",
                    VolumeSize = 30
                )
            )
        ],
        CreditSpecification = LaunchTemplateCreditSpecification(
            CpuCredits = "Unlimited"
        ),
        InstanceType = "t3.micro",
        IamInstanceProfile = IamInstanceProfile(
            region.replace("-", "") + "ecsliveiaminstanceprofile",
            Arn = GetAtt(ecs_instance_profile, "Arn")
        ),
        KeyName = "live-eu-west-1",
        SecurityGroupIds = [
            GetAtt(security_group, "GroupId")
        ],
        UserData = Base64(
            "#!/bin/bash\n" \
            "/usr/bin/yum install -y awscli && aws s3 cp s3://mgmt.eu-west-1.weblox.io/bootstrap/bootstrap.sh /root/bootstrap.sh && chmod 700 /root/bootstrap.sh && /root/bootstrap.sh\n"
        )
    ),
)

template.add_resource(cluster)
template.add_resource(launch_template)

auto_scaling_group = AutoScalingGroup(
    region.replace("-", "") + "ecsliveautoscalinggroup",
    LaunchTemplate = LaunchTemplateSpecification(
        LaunchTemplateId = Ref(launch_template),
        Version = GetAtt(launch_template, "LatestVersionNumber")
    ),
    MinSize = 1,
    MaxSize = 1,
    VPCZoneIdentifier = [
        "subnet-0777c674d3018efd6",
        "subnet-0dec29b6660100d8d",
        "subnet-095d86cbe447af65e"
    ]
)

template.add_resource(auto_scaling_group)

# TODO: sort out ipv6 on vpc so can use dualstack here
application_load_balancer = LoadBalancer(
    region.replace("-", "") + "ecsliveapplicationloadbalancer",
    IpAddressType = "ipv4",
    LoadBalancerAttributes = [
        LoadBalancerAttributes(
            Key="access_logs.s3.enabled",
            Value = "true"
        ),
        LoadBalancerAttributes(
            Key="access_logs.s3.bucket",
            Value = "mgmt.eu-west-1.weblox.io"
        ),
        LoadBalancerAttributes(
            Key="access_logs.s3.prefix",
            Value = "logs"            
        )
    ],
    Scheme = "internet-facing",
    Subnets = [
        "subnet-0777c674d3018efd6",
        "subnet-0dec29b6660100d8d",
        "subnet-095d86cbe447af65e"
    ],
    Type = "application"
)


template.add_resource(application_load_balancer)


print(template.to_yaml())