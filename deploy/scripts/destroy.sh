(cd ./deploy && terraform init)
(cd ./deploy && terraform destroy -var-file configs/${TF_WORKSPACE}.tfvars)
