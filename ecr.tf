resource "aws_ecr_repository" "ml_app_repo" {
  name                 = "flask-ml-repo"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  tags = {
    Name = "ML-Flask-App-Repo"
  }
}

output "ecr_repository_url" {
  value = aws_ecr_repository.ml_app_repo.repository_url
}