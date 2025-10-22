module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "ml-app-vpc"
  cidr = "10.0.0.0/16"

  azs                  = ["ap-south-1a", "ap-south-1b"]
  public_subnets       = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets      = ["10.0.11.0/24", "10.0.12.0/24"]
  enable_nat_gateway   = true
  single_nat_gateway   = true # Use a single NAT Gateway for cost-effectiveness
}