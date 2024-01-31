import pulumi
import pulumi_aws as aws
import requests
import sys

key_url = 'https://github.com/liyihuang.keys'
cloud_init_url = 'https://raw.githubusercontent.com/liyihuang/liyi-cloudinit/main/liyi-init.cfg'


key_respond = requests.get(key_url)
cloud_init_respond = requests.get(cloud_init_url)

if key_respond.status_code != 200 or cloud_init_respond.status_code != 200:
    sys.exit()
else:
    cloud_init_data = cloud_init_respond.text
    public_key = key_respond.text    


key_pair = aws.ec2.KeyPair("liyi-key", public_key=public_key)

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
    description='Enable SSH access and allow outgoing traffic',
    ingress=[
        {
            'from_port': 22,
            'to_port': 22,
            'protocol': 'tcp',
            'cidr_blocks': ['0.0.0.0/0'],
        },
    ],
    egress=[
        {
            'from_port': 0,
            'to_port':0,
            'protocol': '-1',
            'cidr_blocks': ['0.0.0.0/0'],

        }
    ]
)

liyi_jumpox = aws.ec2.Instance("liyi_jumpbox",
    ami=ubuntu_image.id,
    security_groups=[liyi_jumpbox_sg.name],
    user_data=cloud_init_data,
    instance_type="t3.medium",
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=60,  # Set to the desired size of the root volume in GiB
    ),
    key_name=key_pair.key_name,
    tags={
        "Name": "liyi-aws-jumpbox"}
)


liyi_fqdn = aws.route53.get_zone(name="liyi.cilium.rocks")
jumpbox_fqdn = aws.route53.Record("jumpbox_fqdn",
    zone_id=liyi_fqdn.zone_id,
    name=f"jumpbox.{liyi_fqdn.name}",
    type="A",
    ttl=5,
    records=[liyi_jumpox.public_ip])