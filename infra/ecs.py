import requests

from troposphere import GetAtt, Ref, Template
# from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration
# from troposphere.ec2 import LaunchTemplate
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration, LaunchTemplateSpecification
from troposphere.ec2 import EBSBlockDevice, LaunchTemplate, LaunchTemplateCreditSpecification, LaunchTemplateBlockDeviceMapping, LaunchTemplateData, IamInstanceProfile
from troposphere.ecs import Cluster, ClusterSetting
from troposphere.ec2 import SecurityGroup, SecurityGroupIngress, SecurityGroupRule
from troposphere.iam import Role, Policy, InstanceProfile

from troposphere.ec2 import CreditSpecification

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
        "arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM",
        "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
    ],
    Policies = [
        Policy(
            PolicyName = "ecs-service",
            PolicyDocument = {
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
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
                        "ecr:GetAuthorizationToken"
                    ],
                    "Resource": "*"
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
        ]
    )
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

print(template.to_yaml())