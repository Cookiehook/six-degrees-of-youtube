#!/bin/bash

sudo yum update -y
sudo yum install docker -y
#sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user

docker run \
  -p 5000:500 \
  --restart=always \
  --log-driver=awslogs \
  --log-opt awslogs-region="${aws_region}" \
  --log-opt awslogs-create-group=true \
  --log-opt awslogs-group="six-degrees-of-youtube\${docker_tag}\ec2" \
  --log-opt awslogs-stream="$(curl -s http://169.254.169.254/latest/meta-data/instance-id)" \
  cookiehook/six-degrees-of-youtube:${docker_tag}
