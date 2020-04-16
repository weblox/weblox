from troposphere import Template
from troposphere.route53 import HostedZone


domain = "weblox.io"
region = "eu-west-1"

template = Template(
    domain.replace(".", "") + "dns"
)

public_dns = HostedZone(
    domain.replace(".", "") + "publicdns",
    Name = "public." + domain
)

template.add_resource(public_dns)

print(template.to_json())