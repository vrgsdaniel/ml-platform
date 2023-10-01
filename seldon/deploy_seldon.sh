kubectl create ns ml-models
kubectl config set-context --current --namespace=ml-models
kubectl create secret generic seldon-init-container-secret \
  --from-literal=RCLONE_CONFIG_S3_ACCESS_KEY_ID=${MINIO_USER} \
  --from-literal=RCLONE_CONFIG_S3_SECRET_ACCESS_KEY=${MINIO_PASSWORD} \
  --from-literal=RCLONE_CONFIG_S3_ENDPOINT=http://minio.minio-system.svc.cluster.local:9000 \
  --from-literal=RCLONE_CONFIG_S3_ENV_AUTH=false \
  --from-literal=RCLONE_CONFIG_S3_PROVIDER=minio \
  --from-literal=RCLONE_CONFIG_S3_TYPE=s3 \
  -n ml-models
kubectl create ns seldon-system
kubectl config set-context --current --namespace=seldon-system
helm upgrade --install seldon-core seldon-core-operator \
    --repo https://storage.googleapis.com/seldon-charts \
    --set usageMetrics.enabled=true \
    --namespace seldon-system \
    --set istio.enabled=false