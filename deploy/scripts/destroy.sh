(cd ./deploy && terraform init -upgrade -backend-config="bucket=${TF_S3_BUCKET}" -backend-config="key=workspaces/${TF_WORKSPACE}.tfstate")
(cd ./deploy && terraform destroy -var-file configs/${TF_WORKSPACE}.tfvars)
