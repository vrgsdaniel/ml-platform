source .env
kubectl create ns postgres
helm repo add bitnami https://charts.bitnami.com/bitnami
helm upgrade --install postgresql bitnami/postgresql \
    --set image.tag=13 \
    --set auth.username=${DB_USER} \
    --set auth.password=${DB_PASSWORD} \
    --set auth.database=${DB_NAME} \
    --set primary.initdb.user=${DB_USER} \
    --set primary.initdb.password=${DB_PASSWORD} \
    --set primary.initdb.scripts."schema\.sql"="CREATE SCHEMA IF NOT EXISTS mlflow;ALTER DATABASE mlflowdb SET search_path = mlflow;" \
    --namespace postgres