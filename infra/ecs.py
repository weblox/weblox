from troposphere import GetAtt, Ref, Template
# from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration
# from troposphere.ec2 import LaunchTemplate
from troposphere.autoscaling import AutoScalingGroup, LaunchConfiguration, LaunchTemplateSpecification
from troposphere.ec2 import EBSBlockDevice, LaunchTemplate, LaunchTemplateCreditSpecification, LaunchTemplateBlockDeviceMapping, LaunchTemplateData
from troposphere.ecs import Cluster, ClusterSetting

from troposphere.ec2 import CreditSpecification

image_id = "ami-09cec0d91e6d220ea"
region = "eu-west-1"


template = Template()
template.set_version("2010-09-09")

ecs_cluster = Cluster(
    region.replace("-", "") + "ecslive",
    ClusterName = "live",
    ClusterSettings = [
        ClusterSetting(
            Name = "containerInsights",
            Value = "enabled"
        )
    ]
)

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
        InstanceType = "t3.micro"
    )
)

template.add_resource(ecs_cluster)
template.add_resource(launch_template)

auto_scaling_group = AutoScalingGroup(
    region.replace("-", "") + "ecsliveautoscalinggroup",
    LaunchTemplate = LaunchTemplateSpecification(
        LaunchTemplateId = Ref(launch_template),
        Version = GetAtt(launch_template, "LatestVersionNumber")
    ),
    MinSize = 0,
    MaxSize = 0,
    VPCZoneIdentifier = [
        "subnet-0777c674d3018efd6",
        "subnet-0dec29b6660100d8d",
        "subnet-095d86cbe447af65e"
    ]
)
# Exactly one of [LaunchConfigurationName,InstanceId,LaunchTemplate,MixedInstancesPolicy] needs to be specified


template.add_resource(auto_scaling_group)

print(template.to_yaml())