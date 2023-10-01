source .env
kubectl create ns minio-system
helm repo add minio https://helm.min.io/
helm upgrade --install minio minio/minio \
--set accessKey=${MINIO_USER} \
--set secretKey=${MINIO_PASSWORD} \
--values ./values.yaml \
--namespace minio-system