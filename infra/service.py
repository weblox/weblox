from troposphere import Base64, GetAtt, Ref, Join, Sub, Template
from troposphere.elasticloadbalancingv2 import Action, Condition, ListenerRule, TargetGroup
from troposphere.ecs import TaskDefinition, Service, ContainerDefinition, PortMapping, LoadBalancer

template = Template(
    "testservice"
)

vpc_id = "vpc-0e2786487ff4f2ef4"
region = "eu-west-1"

test_target_group = TargetGroup(
    "targetgroup",
    Name = "service-live",
    Port = 80,
    Protocol = "HTTP",
    TargetType = "instance",
    VpcId = vpc_id
)
template.add_resource(test_target_group)

listener_rule = ListenerRule(
    "listenerrule",
    Actions = [
        Action(
            TargetGroupArn = Ref(test_target_group),
            Type = 'forward'
        )
    ],
    Conditions = [
        Condition(
            Field = "path-pattern",
            Values = [
                "/"
            ]
        )
    ],
    Priority = 1,
    ListenerArn = "arn:aws:elasticloadbalancing:eu-west-1:837380460554:listener/app/live-euwes-14F0KA84VQMOV/95ccdb141691f73e/01a71f7b4d1f6a1d"
)

template.add_resource(listener_rule)

test_task_definition = TaskDefinition(
    "taskdefinition",
    ContainerDefinitions = [
        ContainerDefinition(
            DockerLabels = {},
            Environment = [],
            Image = "nginxdemos/hello",
            Name = "helloworld",
            MemoryReservation = 64,
            PortMappings = [
                PortMapping(
                    "httpportmapping",
                    ContainerPort = 80,
                    Protocol = "tcp"
                )
            ]
        )
    ]
)

template.add_resource(test_task_definition)

service = Service(
    "service",
    Cluster = "live",
    DesiredCount = 1,
    LaunchType = "EC2",
    LoadBalancers = [
        LoadBalancer(
            "serviceloadbalancer",
            ContainerName = "helloworld",
            ContainerPort = 80,
            TargetGroupArn = Ref(test_target_group)
        )
    ],
    SchedulingStrategy = "REPLICA",
    ServiceName = "helloworld",
    TaskDefinition = Ref(test_task_definition)
)

template.add_resource(service)

print(template.to_yaml())

# {
#   "Type" : "AWS::ECS::TaskDefinition",
#   "Properties" : {
#       "ContainerDefinitions" : [ ContainerDefinition, ... ],
#       "Cpu" : String,
#       "ExecutionRoleArn" : String,
#       "Family" : String,
#       "InferenceAccelerators" : [ InferenceAccelerator, ... ],
#       "IpcMode" : String,
#       "Memory" : String,
#       "NetworkMode" : String,
#       "PidMode" : String,
#       "PlacementConstraints" : [ TaskDefinitionPlacementConstraint, ... ],
#       "ProxyConfiguration" : ProxyConfiguration,
#       "RequiresCompatibilities" : [ String, ... ],
#       "Tags" : [ Tag, ... ],
#       "TaskRoleArn" : String,
#       "Volumes" : [ Volume, ... ]
#     }
# }