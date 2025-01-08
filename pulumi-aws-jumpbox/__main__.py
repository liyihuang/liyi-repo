import sys
import os

import time
import pulumi
import pulumi_aws as aws
import requests



config = pulumi.Config()

enable_syncthing = config.get_bool("enable_syncthing")  or False

key_url = 'https://github.com/liyihuang.keys'
cloud_init_url = 'https://raw.githubusercontent.com/liyihuang/liyi-cloudinit/main/liyi-init.cfg'
external_ip = requests.get('https://api.ipify.org', timeout=5).content.decode('utf8')+'/32'
key_respond = requests.get(key_url,timeout=5)
cloud_init_respond = requests.get(cloud_init_url,timeout=5)


def setup_local_syncthing(jumpbox_fqdn_id):
    while True:
        try:
            response = requests.get(cloud_init_syncid_url, timeout=5)
            if response.status_code == 200:
                print("syncid is now accessible!")
                sync_id = response.text
                break
            else:
                print("Waiting for syncid to be accessible...")
                time.sleep(1)
        except Exception as e:
            print(f"Error occurred while checking syncid {e}")
            time.sleep(1)
    print("start to run local syncthing")
    # Run a simple shell command
    os.system(f"syncthing cli config devices add --device-id {sync_id}")
    os.system(f"syncthing cli config folders default devices add --device-id {sync_id}")


if key_respond.status_code != 200 or cloud_init_respond.status_code != 200:
    sys.exit()
else:
    cloud_init_data = cloud_init_respond.text.replace('liyi-linux','aws_liyi_jumpbox')
    public_key = key_respond.text

liyi_tags = {'expiry':'2026-01-01','owner':'liyi.huang@isovalent.com'}
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
    user_data=cloud_init_data,
    instance_type="t3.xlarge",
    root_block_device=aws.ec2.InstanceRootBlockDeviceArgs(
        volume_size=60,  # Set to the desired size of the root volume in GiB
    ),
    key_name=key_pair.key_name,
    tags=liyi_tags
)


jumpbox_public_ip = aws.ec2.Instance.get("jumpbox_public_ip",liyi_jumpox.id).public_ip

liyi_fqdn = aws.route53.get_zone(name="liyi.cilium.rocks")
jumpbox_liyi_fqdn = 'jumpbox.'+aws.route53.get_zone(name="liyi.cilium.rocks").name

jumpbox_fqdn = aws.route53.Record("jumpbox_fqdn",
    zone_id=liyi_fqdn.zone_id,
    name=jumpbox_liyi_fqdn,
    type="A",
    ttl=5,
    records=[jumpbox_public_ip])
if enable_syncthing:
    cloud_init_http_server_url = 'http://'+jumpbox_liyi_fqdn+':8000/'
    cloud_init_syncid_url = cloud_init_http_server_url+'syncid'
    jumpbox_fqdn.id.apply(setup_local_syncthing)
    pulumi.export("syncthing_status", "Syncthing is enabled and running.")
else:
    pulumi.export("syncthings_status", "Syncthing is disabled.")
