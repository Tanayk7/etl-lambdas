call config.bat
aws ecr get-login-password --region %aws_region% | docker login --username AWS --password-stdin %account_id%.dkr.ecr.%aws_region%.amazonaws.com 
aws ecr create-repository --repository-name %docker_image_name% --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE 