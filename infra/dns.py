from troposphere import Template
from troposphere.route53 import HostedZone, HostedZoneVPCs


domain = "weblox.io"
region = "eu-west-1"

template = Template(
    domain.replace(".", "") + "dns"
)

public_dns = HostedZone(
    domain.replace(".", "") + "publicdns",
    Name = "public." + region + "." + domain
)

private_dns = HostedZone(
    domain.replace(".", "") + "privatedns",
    Name = "private." + region + "." + domain,
    VPCs = [
        HostedZoneVPCs(
            VPCId = "vpc-0e2786487ff4f2ef4",
            VPCRegion = "eu-west-1"
        )
    ]
)

template.add_resource(public_dns)
template.add_resource(private_dns)

print(template.to_yaml())