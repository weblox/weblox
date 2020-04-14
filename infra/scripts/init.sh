#!/usr/bin/sh
/usr/bin/yum install -y amazon-ssm-agent aws-cfn-bootstrap hibagent python3
/usr/bin/yum install -y https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
/usr/bin/enable-ec2-spot-hibernation
/bin/pip3 install awscli boto3 requests
[ -x /usr/local/bin/aws_completer ] && echo "complete -C '/usr/local/bin/aws_completer' aws" > /etc/profile.d/aws.sh

#/bin/python3
#/bin/pip3
#/usr/local/bin/aws

