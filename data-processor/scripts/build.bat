call config.bat
cd ../
docker build -t %docker_username%/%docker_image_name% .
cd scripts