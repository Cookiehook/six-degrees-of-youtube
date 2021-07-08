pipenv run python deploy/scripts/create_artifact.py
aws s3 cp build/lambda.zip s3://${TF_S3_BUCKET}/artifacts/six-degrees-of-youtube/lambda.zip

(cd ./deploy && terraform init)
(cd ./deploy && terraform apply -var-file configs/${TF_WORKSPACE}.tfvars)

aws s3 rm s3://${TF_S3_BUCKET}/artifacts/six-degrees-of-youtube/lambda.zip
