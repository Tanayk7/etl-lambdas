@REM call config.bat
@REM aws ecr get-login-password --region %aws_region% | docker login --username AWS --password-stdin %account_id%.dkr.ecr.%aws_region%.amazonaws.com 
@REM docker tag %docker_username%/%docker_image_name%:latest %account_id%.dkr.ecr.%aws_region%.amazonaws.com/%docker_image_name%:latest
@REM docker push %account_id%.dkr.ecr.%aws_region%.amazonaws.com/%docker_image_name%
@REM aws lambda update-function-code --function-name %docker_image_name% --image-uri %account_id%.dkr.ecr.%aws_region%.amazonaws.com/%docker_image_name%:latest

call config.bat

@REM Login to ECR
aws ecr get-login-password --region %aws_region% | docker login --username AWS --password-stdin %account_id%.dkr.ecr.%aws_region%.amazonaws.com

@REM Tag and push the Docker image to ECR
docker tag %docker_username%/%docker_image_name%:latest %account_id%.dkr.ecr.%aws_region%.amazonaws.com/%docker_image_name%:latest
docker push %account_id%.dkr.ecr.%aws_region%.amazonaws.com/%docker_image_name%

@REM Check if the Lambda function already exists
aws lambda get-function --function-name %docker_image_name% --region %aws_region% >nul 2>&1

IF %ERRORLEVEL% EQU 0 (
    @REM Lambda function exists, so update function code
    echo "Lambda function exists. Updating function code..."
    aws lambda update-function-code --function-name %docker_image_name% --image-uri %account_id%.dkr.ecr.%aws_region%.amazonaws.com/%docker_image_name%:latest --region %aws_region%
) ELSE (
    @REM Lambda function does not exist, so create it
    echo "Lambda function does not exist. Creating a new function..."
    aws lambda create-function --function-name %docker_image_name% --package-type Image --code ImageUri=%account_id%.dkr.ecr.%aws_region%.amazonaws.com/%docker_image_name%:latest --role %lambda_role_arn% --memory-size %lambda_memory_size% --ephemeral-storage "{\"Size\": %lambda_storage_size%}" --timeout %lambda_timeout% --region %aws_region%
)
