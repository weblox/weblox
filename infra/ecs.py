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
            "/usr/bin/yum install -y awscli && aws s3 cp s3://mgmt.eu-west-1.weblox.io/init.sh /root/init.sh && chmod 700 /root/init.sh && /root/init.sh\n"
        )
    ),
    # Metadata=Metadata(
    #     Init({
    #         'config': InitConfig(
    #             files=InitFiles({
    #                 '/etc/cfn/cfn-hup.conf': InitFile(
    #                     content=Join("", 
    #                         [
    #                             "[main]\n",
    #                             "stack=",
    #                             Ref('AWS::StackId'), 
    #                             "\n",
    #                             "region=eu-west-1\n"
    #                         ]
    #                     ),
    #                     mode='000400',
    #                     owner='root',
    #                     group='root'
    #                 ),
    #                 '/etc/cfn/hooks.d/cfn-auto-reloader.conf': InitFile(
    #                     content=Join('', ['[cfn-auto-reloader-hook]\n',
    #                                       'triggers=post.update\n',
    #                                       'path=Resources.ContainerInstances.Metadata.AWS::CloudFormation::Init\n',  # NOQA
    #                                       'action=/opt/aws/bin/cfn-init -v ', '--stack ', Ref(  # NOQA
    #                                           'AWS::StackName'), ' --resource ContainerInstances ', ' --region ', Ref('AWS::Region'), '\n',  # NOQA
    #                                       'runas=root\n']),
    #                     mode='000400',
    #                     owner='root',
    #                     group='root'
    #                 )},
    #             ),
    #             services=InitServices({
    #                 'cfn-hup': InitService(
    #                     ensureRunning='true',
    #                     enabled='true',
    #                     files=['/etc/cfn/cfn-hup.conf',
    #                            '/etc/cfn/hooks.d/cfn-auto-reloader.conf']
    #                 )}
    #             ),
    #             commands={
    #                 '01_add_instance_to_cluster': [
    #                     "#!/bin/bash\n" \
    #                     "echo ECS_CLUSTER=live >> /etc/ecs/ecs.config"
    #                 ],
    #                 '02_install_ssm_agent': {'command': Join('',
    #                                                          ['#!/bin/bash\n',
    #                                                           'yum -y update\n',  # NOQA
    #                                                           'curl https://amazon-ssm-eu-west-1.s3.amazonaws.com/latest/linux_amd64/amazon-ssm-agent.rpm -o amazon-ssm-agent.rpm\n',  # NOQA
    #                                                           'yum install -y amazon-ssm-agent.rpm'  # NOQA
    #                                                           ])}
    #             }
    #         )
    #     }
    #     ),
    # ),
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