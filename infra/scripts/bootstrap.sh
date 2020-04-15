#!/usr/bin/sh
/usr/bin/yum update -y
/usr/bin/yum install -y awscli amazon-ssm-agent aws-cfn-bootstrap hibagent python3 vim
/usr/bin/yum install -y https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
/usr/bin/enable-ec2-spot-hibernation
/bin/pip3 install boto3 requests
[ -x /usr/bin/aws_completer ] && echo "complete -C '/usr/bin/aws_completer' aws" > /etc/profile.d/aws.sh
/usr/bin/aws s3 cp s3://mgmt.eu-west-1.weblox.io/config/ecs.config /etc/ecs/ecs.config && chmod 644 /etc/ecs/ecs.config

# create ecs config
# create ssm config
# create cloudwatch logs config
