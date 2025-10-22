module "eks_cluster" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "ml-devops-eks-cluster"
  cluster_version = "1.29"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    ml_workers = {
      min_size     = 1
      max_size     = 3
      desired_size = 2
      instance_types = ["t3.medium"]
      iam_role_additional_policies = {
        ecr_read_access = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
      }
    }
  }
}

output "kubeconfig_command" {
  description = "Command to configure kubectl"
  value       = "aws eks --region ap-south-1 update-kubeconfig --name ${module.eks_cluster.cluster_name}"
}