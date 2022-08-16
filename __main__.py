import os
from pathlib import Path

import pulumi
from pulumi_proxmoxve import Provider, ProviderVirtualEnvironmentArgs
from pulumi_proxmoxve.vm import *
import pulumi_command as command
import pulumi_random as random

from diagrams import Cluster, Diagram, Edge
from diagrams.onprem.compute import Server

config = pulumi.Config()
root_password = config.require("root_password")

# The privateKey associated with the selected key must be provided (either directly or base64 encoded)
def decode_key(key):
    try:
        key = base64.b64decode(key.encode("ascii")).decode("ascii")
    except:
        pass
    if key.startswith("-----BEGIN RSA PRIVATE KEY-----"):
        return key
    return key.encode("ascii")


private_key = config.require_secret("privateKey")

# this provider cannot read configuration from Environment variables yet,
# You must manually pass parameters by instantiating a custom provider
proxmox_provider = Provider(
    "proxmox-provider",
    virtual_environment=ProviderVirtualEnvironmentArgs(
        endpoint=os.environ.get("PROXMOX_VE_ENDPOINT"),
        insecure=os.environ.get("PROXMOX_VE_INSECURE"),
        username=os.environ.get("PROXMOX_VE_USERNAME"),
        password=os.environ.get("PROXMOX_VE_PASSWORD"),
    ),
)

## Node1
# create a virtual machine
node1 = VirtualMachine(
    "node01",
    name="node01",
    description="Hashistack Node 01 - Primary",
    node_name="pve",
    on_boot=True,  # start the vm during system bootup
    reboot=False,  # reboot the vm after it was created successfully
    started=True,  # start the vm after it was created successfully
    clone=VirtualMachineCloneArgs(
        vm_id=9000,  # template's vmId
        full=True,  # full clone, not linked clone
        datastore_id="local-lvm",  # template's datastore
        node_name="pve",  # template's node name
    ),
    cpu=VirtualMachineCpuArgs(
        cores=2,
        sockets=2,
        type="host",  # set it to kvm64 for better vm migration
    ),
    memory=VirtualMachineMemoryArgs(dedicated="4096", shared="4096"),  # unit: MB
    operating_system=VirtualMachineOperatingSystemArgs(
        type="l26"  # l26: linux2.6-linux5.x
    ),
    agent=VirtualMachineAgentArgs(enabled=True, timeout="6120s"),
    disks=[
        VirtualMachineDiskArgs(
            interface="scsi0",
            datastore_id="local-lvm",
            size="32",  # unit: GB
        )
    ],
    network_devices=[
        VirtualMachineNetworkDeviceArgs(enabled=True, bridge="vmbr1", model="virtio")
    ],
    # cloud init configuration
    initialization=VirtualMachineInitializationArgs(
        type="nocloud",  # 'nocloud' for linux,  'configdrive2' for windows
        datastore_id="local-lvm",
        dns=VirtualMachineInitializationDnsArgs(
            # dns servers,
            server="1.1.1.1,1.0.0.1",
        ),
        user_account=VirtualMachineInitializationUserAccountArgs(
            # set root's ssh key
            keys=[
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCnKTBL3YL5HphgdAyZVh21O20nuljEtC9d4pqJnr5PU4c/8HM21mu4Sh9DgltA51bsjQ3ZJpt9/Tio/2xwyxS16hEcaNvZq1YauyCHPZhLOpMTSKKkKMt9PUDpG2gRj4qlpd9JOpVovw0wjgrNHJRq+uCZ/I8WKUeoALgdwklRHfCJhK9jKK9rrqeRpI8GnO0YoZcs7DZHBKj1hPZkYdJYs1pfl6UwIeMeihD+6FWKILwmmWavmq/gBsjXYAunDyCJp/y/f9nWzJyn/kcM54ijItpWcgTcJR2YoEJneap7LUFAtPvg3mWvIRj6bUEh1Mywj91MYRi616GLe2bu+FQQufgtsWYCgHrZ+q3W6+ws3PAE1C91Q9GdISqMNXalnVgHSA9VzUlvnwC2v9WYS5tPW1EGn3rY1G2DRgN7KehZ8U/bp/kmdKi+h/l4l2GQY/xzRGUNWkFziyIlmR/+le1xgWYYJXjMdJj/vRkjToS8+yKaAGCNqeSWBenLrdF/0xU= justin@Jump-Box",
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC7N7P0fzmtfpL24RVsJgZ0JCQMXv8aOMPI2I8J1mqsFY32rNeVGqlg3KEqwhevLtgcb1TfuG70kbHvXzFoOSWm5bxBaQ7JMIC5GCsM16yxOh9CvklSr71th1ScZg2NLcEf7LY1k3d6BJ9BfzIhmak4hraDAI0zCTweJSGu+D5a4Ibb5Ii7t0TozL4nuS/asLSK+D2aewGEZ2TbA0boPV+8F+mxW+YBAbJneJ8Qn3h63IZ3sfTIbxUXQx6mzBahZkEW2+nRoSgyAuFRCzvy2b6MJBlcfVm0dgc+qql7MYsjnxAupleYbPyMNZH/VcBAjuRcQ0nveNvmugphsV1r0RGddTpzpE2xvJepNwl69KU3Nwicip3sGAKIFRplPNp0M6YXA6kVU/ug6tuFcZyNhbcLz+EvUtQ4CIGU8Q6fVFdipJPud8S55qKJrMIaZV04u6/jGXM527GjyUXpvkO+UR8tFRUZBCB538Y/lhFPFnNQoBO16jctlGY7dZu23JqyqtjlJnpL7Sj8sJTnbw593QsY5gJt8eaIuh07ekphDFRXje3f5YZqDgQ9hvFXLkKagmooEtS0mB2uE2KgXRb7HahRIgb4Dw5QQG7cKAaJqc8gaVx4YjQ1Q9fxi3k9cLdS641RAW350xcSGlfPEfnGjpXdTS1JYdPV33qS1BpwJQOYVw==",
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCgGzm8DXXFb0Ccu868rz8bWxQhmgnlQ3LDSaxXCvThxW6H0X981KMpM4UCqvP7p1+u4lGC3C6AMK1RdXGIL48RklGBW8+0agYr/f/hiNxHceuZmLw62HLJY7LUtpMeM9Z5NlQnf8KX8qZooS3KPPBatlPVpz9fBRsw9Pk5p089hGxWryrMCLsYF48OaKi29gJqpC27rMF/AGsTk0HlVuEkR8fRLMGs1U2pgHIX1GciLcb4pU/qCzSzaZDr64J0MPD+V/qPDPymSjQd4rZccqg3ApiY87r+Kz9/viAf1s0hQCMBMIFdaBnSsnZpk17cYtwG2I3zfXqHS4fght7sMxpcIExBlQmy3xNy9lQJxV3tVGkCNAMUzzoUCYgFXEPcPPG6hWws0lzNNtQTh7hYZe7CXrAN1MOqGLY4tCno96EFT+laK2pFMq+MSEXe9nJyVAx0pMDyAbFXI2Wf0BW8H7mqFu/cy3IGjf/Rpy3XfwQBRMDNMM26d6RKHKZT74gHUc57+EzZ4nSZd13a/tpJesoIkfTxsgUxAOCwGNPUvNIuc8b9DFwZWj9NPMYh2C/tUV+3WD8CIxH0C4EJ+aeBHJN9HWmcoLEpECHxXqwb9CZiT9WlUuRcIqn75kwH2sFGpMuuG8EZ6/ozqhGMgeAfysZsHJcflo9M3NuTbtEeeuNWMw== cardno:000606943934",
            ],
            password=root_password,  # needed when login from console
            username="root",
        ),
    ),
    # use custom provider
    opts=pulumi.ResourceOptions(provider=proxmox_provider),
)

pulumi.export("IPv4_address_node1", node1.ipv4_addresses[1][0])

connection_node1 = command.remote.ConnectionArgs(
    host=node1.ipv4_addresses[1][0], user="root", private_key=private_key
)

hostname_node1 = command.remote.Command(
    "setHostname_node1",
    connection=connection_node1,
    create="hostnamectl set-hostname node1",
    opts=pulumi.ResourceOptions(depends_on=[node1]),
)

install_consul_node1 = command.remote.Command(
    "install_consul_node1",
    connection=connection_node1,
    create="yum install -y yum-utils && yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo && yum -y install consul",
    opts=pulumi.ResourceOptions(depends_on=[node1]),
)

config_consul_node1 = command.remote.Command(
    "config_consul_node1", connection=connection_node1, create=""
)

## Node2
# create a virtual machine
node2 = VirtualMachine(
    "node02",
    name="node02",
    description="Hashistack Node 02 - Primary",
    node_name="pve",
    on_boot=True,  # start the vm during system bootup
    reboot=False,  # reboot the vm after it was created successfully
    started=True,  # start the vm after it was created successfully
    clone=VirtualMachineCloneArgs(
        vm_id=9000,  # template's vmId
        full=True,  # full clone, not linked clone
        datastore_id="local-lvm",  # template's datastore
        node_name="pve",  # template's node name
    ),
    cpu=VirtualMachineCpuArgs(
        cores=2,
        sockets=2,
        type="host",  # set it to kvm64 for better vm migration
    ),
    memory=VirtualMachineMemoryArgs(dedicated="4096", shared="4096"),  # unit: MB
    operating_system=VirtualMachineOperatingSystemArgs(
        type="l26"  # l26: linux2.6-linux5.x
    ),
    agent=VirtualMachineAgentArgs(enabled=True, timeout="6120s"),
    disks=[
        VirtualMachineDiskArgs(
            interface="scsi0",
            datastore_id="local-lvm",
            size="32",  # unit: GB
        )
    ],
    network_devices=[
        VirtualMachineNetworkDeviceArgs(enabled=True, bridge="vmbr1", model="virtio")
    ],
    # cloud init configuration
    initialization=VirtualMachineInitializationArgs(
        type="nocloud",  # 'nocloud' for linux,  'configdrive2' for windows
        datastore_id="local-lvm",
        dns=VirtualMachineInitializationDnsArgs(
            # dns servers,
            server="1.1.1.1,1.0.0.1",
        ),
        user_account=VirtualMachineInitializationUserAccountArgs(
            # set root's ssh key
            keys=[
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCnKTBL3YL5HphgdAyZVh21O20nuljEtC9d4pqJnr5PU4c/8HM21mu4Sh9DgltA51bsjQ3ZJpt9/Tio/2xwyxS16hEcaNvZq1YauyCHPZhLOpMTSKKkKMt9PUDpG2gRj4qlpd9JOpVovw0wjgrNHJRq+uCZ/I8WKUeoALgdwklRHfCJhK9jKK9rrqeRpI8GnO0YoZcs7DZHBKj1hPZkYdJYs1pfl6UwIeMeihD+6FWKILwmmWavmq/gBsjXYAunDyCJp/y/f9nWzJyn/kcM54ijItpWcgTcJR2YoEJneap7LUFAtPvg3mWvIRj6bUEh1Mywj91MYRi616GLe2bu+FQQufgtsWYCgHrZ+q3W6+ws3PAE1C91Q9GdISqMNXalnVgHSA9VzUlvnwC2v9WYS5tPW1EGn3rY1G2DRgN7KehZ8U/bp/kmdKi+h/l4l2GQY/xzRGUNWkFziyIlmR/+le1xgWYYJXjMdJj/vRkjToS8+yKaAGCNqeSWBenLrdF/0xU= justin@Jump-Box",
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC7N7P0fzmtfpL24RVsJgZ0JCQMXv8aOMPI2I8J1mqsFY32rNeVGqlg3KEqwhevLtgcb1TfuG70kbHvXzFoOSWm5bxBaQ7JMIC5GCsM16yxOh9CvklSr71th1ScZg2NLcEf7LY1k3d6BJ9BfzIhmak4hraDAI0zCTweJSGu+D5a4Ibb5Ii7t0TozL4nuS/asLSK+D2aewGEZ2TbA0boPV+8F+mxW+YBAbJneJ8Qn3h63IZ3sfTIbxUXQx6mzBahZkEW2+nRoSgyAuFRCzvy2b6MJBlcfVm0dgc+qql7MYsjnxAupleYbPyMNZH/VcBAjuRcQ0nveNvmugphsV1r0RGddTpzpE2xvJepNwl69KU3Nwicip3sGAKIFRplPNp0M6YXA6kVU/ug6tuFcZyNhbcLz+EvUtQ4CIGU8Q6fVFdipJPud8S55qKJrMIaZV04u6/jGXM527GjyUXpvkO+UR8tFRUZBCB538Y/lhFPFnNQoBO16jctlGY7dZu23JqyqtjlJnpL7Sj8sJTnbw593QsY5gJt8eaIuh07ekphDFRXje3f5YZqDgQ9hvFXLkKagmooEtS0mB2uE2KgXRb7HahRIgb4Dw5QQG7cKAaJqc8gaVx4YjQ1Q9fxi3k9cLdS641RAW350xcSGlfPEfnGjpXdTS1JYdPV33qS1BpwJQOYVw==",
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCgGzm8DXXFb0Ccu868rz8bWxQhmgnlQ3LDSaxXCvThxW6H0X981KMpM4UCqvP7p1+u4lGC3C6AMK1RdXGIL48RklGBW8+0agYr/f/hiNxHceuZmLw62HLJY7LUtpMeM9Z5NlQnf8KX8qZooS3KPPBatlPVpz9fBRsw9Pk5p089hGxWryrMCLsYF48OaKi29gJqpC27rMF/AGsTk0HlVuEkR8fRLMGs1U2pgHIX1GciLcb4pU/qCzSzaZDr64J0MPD+V/qPDPymSjQd4rZccqg3ApiY87r+Kz9/viAf1s0hQCMBMIFdaBnSsnZpk17cYtwG2I3zfXqHS4fght7sMxpcIExBlQmy3xNy9lQJxV3tVGkCNAMUzzoUCYgFXEPcPPG6hWws0lzNNtQTh7hYZe7CXrAN1MOqGLY4tCno96EFT+laK2pFMq+MSEXe9nJyVAx0pMDyAbFXI2Wf0BW8H7mqFu/cy3IGjf/Rpy3XfwQBRMDNMM26d6RKHKZT74gHUc57+EzZ4nSZd13a/tpJesoIkfTxsgUxAOCwGNPUvNIuc8b9DFwZWj9NPMYh2C/tUV+3WD8CIxH0C4EJ+aeBHJN9HWmcoLEpECHxXqwb9CZiT9WlUuRcIqn75kwH2sFGpMuuG8EZ6/ozqhGMgeAfysZsHJcflo9M3NuTbtEeeuNWMw== cardno:000606943934",
            ],
            password=root_password,  # needed when login from console
            username="root",
        ),
    ),
    # use custom provider
    opts=pulumi.ResourceOptions(provider=proxmox_provider),
)

pulumi.export("IPv4_address_node2", node2.ipv4_addresses[1][0])

connection_node2 = command.remote.ConnectionArgs(
    host=node2.ipv4_addresses[1][0], user="root", private_key=private_key
)

hostname_node2 = command.remote.Command(
    "setHostname_node2",
    connection=connection_node2,
    create="hostnamectl set-hostname node2",
    opts=pulumi.ResourceOptions(depends_on=[node2]),
)

install_consul_node2 = command.remote.Command(
    "install_consul_node2",
    connection=connection_node2,
    create="yum install -y yum-utils && yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo && yum -y install consul",
    opts=pulumi.ResourceOptions(depends_on=[node2]),
)

## Node3
# create a virtual machine
node3 = VirtualMachine(
    "node03",
    name="node03",
    description="Hashistack Node 03 - Primary",
    node_name="pve",
    on_boot=True,  # start the vm during system bootup
    reboot=False,  # reboot the vm after it was created successfully
    started=True,  # start the vm after it was created successfully
    clone=VirtualMachineCloneArgs(
        vm_id=9000,  # template's vmId
        full=True,  # full clone, not linked clone
        datastore_id="local-lvm",  # template's datastore
        node_name="pve",  # template's node name
    ),
    cpu=VirtualMachineCpuArgs(
        cores=2,
        sockets=2,
        type="host",  # set it to kvm64 for better vm migration
    ),
    memory=VirtualMachineMemoryArgs(dedicated="4096", shared="4096"),  # unit: MB
    operating_system=VirtualMachineOperatingSystemArgs(
        type="l26"  # l26: linux2.6-linux5.x
    ),
    agent=VirtualMachineAgentArgs(enabled=True, timeout="6120s"),
    disks=[
        VirtualMachineDiskArgs(
            interface="scsi0",
            datastore_id="local-lvm",
            size="32",  # unit: GB
        )
    ],
    network_devices=[
        VirtualMachineNetworkDeviceArgs(enabled=True, bridge="vmbr1", model="virtio")
    ],
    # cloud init configuration
    initialization=VirtualMachineInitializationArgs(
        type="nocloud",  # 'nocloud' for linux,  'configdrive2' for windows
        datastore_id="local-lvm",
        dns=VirtualMachineInitializationDnsArgs(
            # dns servers,
            server="1.1.1.1,1.0.0.1",
        ),
        user_account=VirtualMachineInitializationUserAccountArgs(
            # set root's ssh key
            keys=[
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCnKTBL3YL5HphgdAyZVh21O20nuljEtC9d4pqJnr5PU4c/8HM21mu4Sh9DgltA51bsjQ3ZJpt9/Tio/2xwyxS16hEcaNvZq1YauyCHPZhLOpMTSKKkKMt9PUDpG2gRj4qlpd9JOpVovw0wjgrNHJRq+uCZ/I8WKUeoALgdwklRHfCJhK9jKK9rrqeRpI8GnO0YoZcs7DZHBKj1hPZkYdJYs1pfl6UwIeMeihD+6FWKILwmmWavmq/gBsjXYAunDyCJp/y/f9nWzJyn/kcM54ijItpWcgTcJR2YoEJneap7LUFAtPvg3mWvIRj6bUEh1Mywj91MYRi616GLe2bu+FQQufgtsWYCgHrZ+q3W6+ws3PAE1C91Q9GdISqMNXalnVgHSA9VzUlvnwC2v9WYS5tPW1EGn3rY1G2DRgN7KehZ8U/bp/kmdKi+h/l4l2GQY/xzRGUNWkFziyIlmR/+le1xgWYYJXjMdJj/vRkjToS8+yKaAGCNqeSWBenLrdF/0xU= justin@Jump-Box",
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC7N7P0fzmtfpL24RVsJgZ0JCQMXv8aOMPI2I8J1mqsFY32rNeVGqlg3KEqwhevLtgcb1TfuG70kbHvXzFoOSWm5bxBaQ7JMIC5GCsM16yxOh9CvklSr71th1ScZg2NLcEf7LY1k3d6BJ9BfzIhmak4hraDAI0zCTweJSGu+D5a4Ibb5Ii7t0TozL4nuS/asLSK+D2aewGEZ2TbA0boPV+8F+mxW+YBAbJneJ8Qn3h63IZ3sfTIbxUXQx6mzBahZkEW2+nRoSgyAuFRCzvy2b6MJBlcfVm0dgc+qql7MYsjnxAupleYbPyMNZH/VcBAjuRcQ0nveNvmugphsV1r0RGddTpzpE2xvJepNwl69KU3Nwicip3sGAKIFRplPNp0M6YXA6kVU/ug6tuFcZyNhbcLz+EvUtQ4CIGU8Q6fVFdipJPud8S55qKJrMIaZV04u6/jGXM527GjyUXpvkO+UR8tFRUZBCB538Y/lhFPFnNQoBO16jctlGY7dZu23JqyqtjlJnpL7Sj8sJTnbw593QsY5gJt8eaIuh07ekphDFRXje3f5YZqDgQ9hvFXLkKagmooEtS0mB2uE2KgXRb7HahRIgb4Dw5QQG7cKAaJqc8gaVx4YjQ1Q9fxi3k9cLdS641RAW350xcSGlfPEfnGjpXdTS1JYdPV33qS1BpwJQOYVw==",
                "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCgGzm8DXXFb0Ccu868rz8bWxQhmgnlQ3LDSaxXCvThxW6H0X981KMpM4UCqvP7p1+u4lGC3C6AMK1RdXGIL48RklGBW8+0agYr/f/hiNxHceuZmLw62HLJY7LUtpMeM9Z5NlQnf8KX8qZooS3KPPBatlPVpz9fBRsw9Pk5p089hGxWryrMCLsYF48OaKi29gJqpC27rMF/AGsTk0HlVuEkR8fRLMGs1U2pgHIX1GciLcb4pU/qCzSzaZDr64J0MPD+V/qPDPymSjQd4rZccqg3ApiY87r+Kz9/viAf1s0hQCMBMIFdaBnSsnZpk17cYtwG2I3zfXqHS4fght7sMxpcIExBlQmy3xNy9lQJxV3tVGkCNAMUzzoUCYgFXEPcPPG6hWws0lzNNtQTh7hYZe7CXrAN1MOqGLY4tCno96EFT+laK2pFMq+MSEXe9nJyVAx0pMDyAbFXI2Wf0BW8H7mqFu/cy3IGjf/Rpy3XfwQBRMDNMM26d6RKHKZT74gHUc57+EzZ4nSZd13a/tpJesoIkfTxsgUxAOCwGNPUvNIuc8b9DFwZWj9NPMYh2C/tUV+3WD8CIxH0C4EJ+aeBHJN9HWmcoLEpECHxXqwb9CZiT9WlUuRcIqn75kwH2sFGpMuuG8EZ6/ozqhGMgeAfysZsHJcflo9M3NuTbtEeeuNWMw== cardno:000606943934",
            ],
            password=root_password,  # needed when login from console
            username="root",
        ),
    ),
    # use custom provider
    opts=pulumi.ResourceOptions(provider=proxmox_provider),
)

pulumi.export("IPv4_address_node3", node3.ipv4_addresses[1][0])

connection_node3 = command.remote.ConnectionArgs(
    host=node3.ipv4_addresses[1][0], user="root", private_key=private_key
)

hostname_node3 = command.remote.Command(
    "setHostname_node3",
    connection=connection_node3,
    create="hostnamectl set-hostname node3",
    opts=pulumi.ResourceOptions(depends_on=[node3]),
)

install_consul_node3 = command.remote.Command(
    "install_consul_node3",
    connection=connection_node3,
    create="yum install -y yum-utils && yum-config-manager --add-repo https://rpm.releases.hashicorp.com/RHEL/hashicorp.repo && yum -y install consul",
    opts=pulumi.ResourceOptions(depends_on=[node3]),
)

with Diagram(name="Hashistack", show=False):
    with Cluster("Master Cluster"):
        grpcsvc = [
            Server("Node1"),
            Server("Node2"),
            Server("Node3"),
        ]
