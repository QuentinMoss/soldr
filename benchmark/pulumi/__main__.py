import pulumi
import pulumi_gcp as gcp

# Import the program's configuration settings.
config = pulumi.Config()
machine_type = config.get("machineType", "n1-standard-1")
client_machine_type = config.get("machineType", "n1-standard-1")
os_image = config.get("osImage", "debian-12")
instance_tag = config.get("instanceTag", "soldr-service")
service_port = config.get("servicePort", "3000")

# Create a new network for the virtual machine.
network = gcp.compute.Network(
    "network",
    gcp.compute.NetworkArgs(
        auto_create_subnetworks=False,
    ),
)

# Create a subnet on the network.
subnet = gcp.compute.Subnetwork(
    "subnet",
    gcp.compute.SubnetworkArgs(
        ip_cidr_range="10.0.1.0/24",
        network=network.id,
    ),
)

# Create a firewall allowing inbound access over ports 80 (for HTTP) and 22 (for SSH).
firewall = gcp.compute.Firewall(
    "firewall",
    gcp.compute.FirewallArgs(
        network=network.self_link,
        allows=[
            gcp.compute.FirewallAllowArgs(
                protocol="tcp",
                ports=[
                    "22",
                    service_port,
                ],
            ),
        ],
        direction="INGRESS",
        source_ranges=[
            "0.0.0.0/0",
        ],
        target_tags=[
            instance_tag,
        ],
    ),
)

# Define a script to be run when the VM starts up.
soldr_service_metadata_startup_script = """
#!/bin/bash
apt update && apt install git build-essential pkg-config lib-ssldev -y &&
sudo -u hadouken bash -c "
    cd ~ &&
    curl https://sh.rustup.rs -sSf | sh -s -- -y &&
    git clone git@github.com:QuentinMoss/soldr.git &&
    source ~/.cargo/env &&
"
"""

soldr_client_metadata_startup_script = """
#!/bin/bash
sudo -u hadouken bash -c "
    sudo apt install git pkg-config -y && 
    cd ~ &&
    curl https://sh.rustup.rs -sSf | sh -s -- -y &&
    git clone https://github.com/hjr3/soldr.git && 
    source ~/.cargo/env &&
    cargo install drill
"
"""

# Create the virtual machine.
soldr = gcp.compute.Instance(
    "soldr-service",
    gcp.compute.InstanceArgs(
        machine_type=machine_type,
        boot_disk=gcp.compute.InstanceBootDiskArgs(
            initialize_params=gcp.compute.InstanceBootDiskInitializeParamsArgs(
                image=os_image,
                type="pd-ssd",
            ),
        ),
        network_interfaces=[
            gcp.compute.InstanceNetworkInterfaceArgs(
                network=network.id,
                subnetwork=subnet.id,
                access_configs=[
                    {},
                ],
            ),
        ],
        service_account=gcp.compute.InstanceServiceAccountArgs(
            scopes=[
                "https://www.googleapis.com/auth/cloud-platform",
            ],
        ),
        allow_stopping_for_update=True,
        tags=[
            instance_tag,
        ],
        metadata_startup_script=soldr_service_metadata_startup_script,
    ),
    pulumi.ResourceOptions(depends_on=firewall),
)

#client = gcp.compute.Instance(
#    "soldr-client",
#    gcp.compute.InstanceArgs(
#        machine_type=client_machine_type,
#        boot_disk=gcp.compute.InstanceBootDiskArgs(
#            initialize_params=gcp.compute.InstanceBootDiskInitializeParamsArgs(
#                image=os_image,
#            ),
#        ),
#        network_interfaces=[
#            gcp.compute.InstanceNetworkInterfaceArgs(
#                network=network.id,
#                subnetwork=subnet.id,
#                access_configs=[
#                    {},
#                ],
#            ),
#        ],
#        service_account=gcp.compute.InstanceServiceAccountArgs(
#            scopes=[
#                "https://www.googleapis.com/auth/cloud-platform",
#            ],
#        ),
#        allow_stopping_for_update=True,
#        metadata_startup_script=soldr_client_metadata_startup_script,
#        tags=[
#            instance_tag,
#        ],
#    ),
#    pulumi.ResourceOptions(depends_on=firewall),
#)
#
soldr_service_ip = soldr.network_interfaces.apply(
    lambda interfaces: interfaces[0].access_configs[0].nat_ip
)

#soldr_client_ip = client.network_interfaces.apply(
#    lambda interfaces: interfaces[0].access_configs[0].nat_ip
#)

# Export soldr client details
#pulumi.export("name", client.name)
#pulumi.export("ip", soldr_client_ip)
#pulumi.export("url", soldr_client_ip.apply(lambda ip: f"http://{ip}:{service_port}"))

# Export soldr-service details
pulumi.export("name", soldr.name)
pulumi.export("ip", soldr_service_ip)
pulumi.export("url", soldr_service_ip.apply(lambda ip: f"http://{ip}:{service_port}"))
