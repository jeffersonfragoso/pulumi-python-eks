"""A Python Pulumi program"""
import pulumi
from pulumi_docker import Image, Registry
import pulumi_awsx as awsx
import pulumi_eks as eks
from pulumi import ResourceOptions
from pulumi_kubernetes import Provider
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs
from pulumi_kubernetes.core.v1 import (
  ContainerArgs,
  ContainerPortArgs,
  PodSpecArgs,
  PodTemplateSpecArgs,
  Service,
  ServiceSpecArgs,
  ServicePortArgs,
)

from config import (
    docker_user_name,
    docker_password,
    eks_node_instance_type,
    desired_cluster_size,
    min_cluster_size,
    max_cluster_size
)

# Build and push docker image
app_image = Image(
    name="docker-image-resource",
    image_name=f'{docker_user_name}/teste-pulumi',
    build="../",
    registry=Registry(
      registry="docekr.io",
      username=docker_user_name,
      password=docker_password
    )
)

# Create a VPC for the EKS cluster
eks_vpc = awsx.ec2.Vpc(
	resource_name="vpc-pulumi",
	number_of_availability_zones=2,
	tags={"Name": "pulmi-vpc"}
)

# Create the EKS cluster
eks_cluster = eks.Cluster(
    resource_name="eks-pulumi",
    vpc_id=eks_vpc.vpc_id,
    tags={"Name": "cluster-pulumi-teste"},
    public_subnet_ids=eks_vpc.public_subnet_ids,
    private_subnet_ids=eks_vpc.private_subnet_ids,
    instance_type=eks_node_instance_type,
    desired_capacity=desired_cluster_size,
    min_size=min_cluster_size,
    max_size=max_cluster_size,
    storage_classes="gp2",
    node_associate_public_ip_address=False,
)

# Create k8s provider
provider = Provider(
    resource_name="eks-provider",
    cluster=eks_cluster,
    kubeconfig=eks_cluster.kubeconfig_json
)


# Create k8s deployment
name = "pulumi-deploy"
app_labels = { "app": "deploy-pulumi" }

deployment = Deployment(
    resource_name="debts-search-deployment",
    metadata=ObjectMetaArgs(labels=app_labels),
    spec=DeploymentSpecArgs(
        selector=LabelSelectorArgs(match_labels=app_labels),
        replicas=1,
        template=PodTemplateSpecArgs(
            metadata=ObjectMetaArgs(labels=app_labels),
            spec=PodSpecArgs(
              containers=[
                ContainerArgs(
                  name=f"app-{name}",
                  image=app_image.base_image_name,
                  ports=[ContainerPortArgs(
                    container_port=80,
                  )]
                )
              ]
            )
        )
    ),
    opts=ResourceOptions(provider=eks_cluster.aws_provider)
)

# Expose the Deployment as a Kubernetes Service
service = Service(
    resource_name=f'service-{name}',
    spec=ServiceSpecArgs(
      type="LoadBalancer",
      ports=[ServicePortArgs(
          port=80,
          target_port=8080,
          protocol="TCP",
      )],
      selector=app_labels,
    ),
    opts=ResourceOptions(provider=eks_cluster.aws_provider)
)

# Export values to use elsewhere
pulumi.export("vpcId", eks_vpc.vpc_id)
pulumi.export("ClusterName", eks_cluster.core.tags)
pulumi.export("kubeconfig", eks_cluster.kubeconfig)
pulumi.export("endpoint_service", service.status.apply(lambda s: f"{s.load_balancer.ingress[0].ip}:{80}"))
pulumi.export("service_host", service.status.load_balancer.ingress[0].hostname)
