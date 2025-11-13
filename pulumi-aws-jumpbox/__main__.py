import sys
import os

import time
import pulumi
import pulumi_aws as aws
import requests



config = pulumi.Config()


external_ip = requests.get('https://api.ipify.org', timeout=5).content.decode('utf8')+'/32'

key_url = 'https://github.com/liyihuang.keys'
public_key = requests.get(key_url,timeout=5).text

fqdn_zone_name = 'cs.isovalent.tech'
fqdn_zone = aws.route53.get_zone(name=fqdn_zone_name)
jumpbox_fqdn = 'liyijumpbox.'+fqdn_zone.name

liyi_tags = {'expiry':'2026-01-01','owner':'liyi.huang@isovalent.com', 'svic_osquery_supported': 'no', 'svic_falco_supported': 'no' }
key_pair = aws.ec2.KeyPair("liyi-key", public_key=public_key,tags=liyi_tags)

ubuntu_image = aws.ec2.get_ami(most_recent=True,
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="virtualization-type",
            values=["hvm"],
        ),
    ],
    owners=["099720109477"])

liyi_jumpbox_sg = aws.ec2.SecurityGroup('liyi_jumpbox_security_group',
    description='Enable incoming traffic and allow outgoing traffic',
    ingress=[
        {
            'from_port': 0,
            'to_port': 0,
            'protocol': '-1',
            'cidr_blocks': [external_ip],
        },
    ],
    egress=[
        {
            'from_port': 0,
            'to_port':0,
            'protocol': '-1',
            'cidr_blocks': ['0.0.0.0/0'],

        }
    ],
    tags=liyi_tags
)

liyi_jumpox = aws.ec2.Instance("liyi_jumpbox",
    ami=ubuntu_image.id,
    security_groups=[liyi_jumpbox_sg.name],
    instance_type="t3.large",
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=60,  # Set to the desired size of the root volume in GiB
    ),
    key_name=key_pair.key_name,
    tags=liyi_tags
)


jumpbox_public_ip = aws.ec2.Instance.get("jumpbox_public_ip",liyi_jumpox.id).public_ip


aws.route53.Record("jumpbox_fqdn",
    zone_id=fqdn_zone.zone_id,
    name=jumpbox_fqdn,
    type="A",
    ttl=5,
    records=[jumpbox_public_ip])

pulumi.export("instance_id", liyi_jumpox.id)
pulumi.export("jumpbox_public_ip", jumpbox_public_ip)
