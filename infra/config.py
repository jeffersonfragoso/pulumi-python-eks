from pulumi import Config

config = Config()


# Docker config
docker_user_name = config.require('DOCKER_USER_NAME')
docker_password = config.require('DOCKER_PASSWORD')

# Kubernetes config
min_cluster_size = config.get_float("MIN_CLUSTER_SIZE", 2)
max_cluster_size = config.get_float("MAX_CLUSTER_SIZE", 2)
desired_cluster_size = config.get_float("DESIRED_CLUSTER_SIZE", 2)
eks_node_instance_type = config.get("EKS_NODE_INSTANCE_TYPE", "t2.micro")
