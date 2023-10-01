source .env
kubectl create ns mlflow
helm repo add community-charts https://community-charts.github.io/helm-charts
helm upgrade --install mlflow community-charts/mlflow \
  --set backendStore.databaseMigration=true \
  --set backendStore.postgres.enabled=true \
  --set backendStore.postgres.host=${DB_HOST} \
  --set backendStore.postgres.port=${DB_PORT} \
  --set backendStore.postgres.database=${DB_NAME} \
  --set backendStore.postgres.user=${DB_USER} \
  --set backendStore.postgres.password=${DB_PASSWORD} \
  --set artifactRoot.proxiedArtifactStorage=true \
  --set artifactRoot.s3.enabled=true \
  --set artifactRoot.s3.bucket=models \
  --set artifactRoot.s3.awsAccessKeyId=${AWS_ACCESS_KEY_ID} \
  --set artifactRoot.s3.awsSecretAccessKey=${AWS_SECRET_ACCESS_KEY} \
  --set extraEnvVars.MLFLOW_S3_ENDPOINT_URL=${MLFLOW_S3_ENDPOINT_URL} \
  --set serviceMonitor.enabled=true \
  --namespace mlflow
  