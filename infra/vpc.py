from ipaddress import ip_network
from troposphere import Ref, Template
from troposphere.ec2 import InternetGateway, Route, RouteTable, Subnet, SubnetCidrBlock, SubnetRouteTableAssociation, VPC, VPCCidrBlock, VPCGatewayAttachment

region = "eu-west-1"
cidr = "10.128.0.0/20"
subnets = list(ip_network(cidr).subnets(prefixlen_diff=4))
zones = ["a", "b", "c"]

template = Template(
    region + " VPC"
)

vpc = VPC(
    region.replace("-", "") + "vpc",
    CidrBlock = cidr,
    EnableDnsHostnames = True,
    EnableDnsSupport = True
)

internet_gateway = InternetGateway(
    region.replace("-", "") + "internetgateway"
)

template.add_resource(vpc)
template.add_resource(internet_gateway)

vpc_gateway_attachment = VPCGatewayAttachment(
    region.replace("-", "") + "vpcgatewayattachment",
    InternetGatewayId = Ref(internet_gateway),
    VpcId = Ref(vpc)
)

template.add_resource(vpc_gateway_attachment)

public_route_table = RouteTable(
    region.replace("-", "") + "publicroutetable",
    VpcId = Ref(vpc)
)

public_route = Route(
    region.replace("-", "") + "publicroute",
    DestinationCidrBlock = "0.0.0.0/0",
    GatewayId = Ref(internet_gateway),
    RouteTableId = Ref(public_route_table)
)

template.add_resource(public_route_table)
template.add_resource(public_route)

i = 0
for zone in zones:
    Subnet(
        'public' + region.replace('-', '') + zone,
        template,
        AvailabilityZone=region + zone,
        CidrBlock=str(subnets[i % len(zones) + 0 * len(zones)]),
        MapPublicIpOnLaunch=True,
        VpcId=Ref(vpc)
    )
    SubnetRouteTableAssociation(
        'public' + region.replace('-', '') + zone + 'subnetroutetableassociation',
        template,
        RouteTableId=Ref(public_route_table),
        SubnetId=Ref('public' + region.replace('-', '') + zone)
    )
    Subnet(
        'private' + region.replace('-', '') + zone,
        template,
        AvailabilityZone=region + zone,
        CidrBlock=str(subnets[i % len(zones) + 1 * len(zones)]),
        MapPublicIpOnLaunch=False,
        VpcId=Ref(vpc)
    )
    i = i + 1

print(template.to_yaml())
