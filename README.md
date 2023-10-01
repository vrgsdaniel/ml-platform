# ML-Platform: an open-source kubernetes native platform for data scientists
Data scientists and Machine-Learning professionals seek empowering tools to experiment, collaborate, and swiftly transition their models into production-ready solutions. Traditionally, organisations have leaned towards major cloud providers to host their workloads, often relying on the ML tools that come with them. While these tools offer substantial benefits, they come with infrastructure costs, vendor lock-in, a challenge of adapting to new releases, and the perpetual quest for comprehensive documentation.

In this article, I will guide you through creating a Kubernetes-native, open-source ML platform. Kubernetes is the go-to orchestration framework for deploying cloud applications efficiently. This platform will empower data scientists to experiment, collaborate, and seamlessly deploy their models as microservices, ready to be integrated into the technological ecosystem. This approach treats data science tools and models as first-class citizens of the Kubernetes ecosystem.

This guide is particularly valuable for:
- ML practitioners interested to delve into Kubernetes and deployment strategies.
- Teams aiming for a portable solution to reduce ML-related cloud costs and willing to allocate initial MLOps resources to maintain the platform.
- Teams with limited existing ML infrastructure open to exploring open-source technologies.

This platform will include the following components:
- MLFlow: Data scientists can use it as a remote tracking server. MLFlow is one of the most popular data science tools for managing reproducible and portable models, sharing them, and versioning them.
- Postgres: For metadata storage, such as data science experiments, runs, model parameters, and metrics. Postgres is a well-known open-source relational database known for its reliability and scalability.
- MinIO: For artifact storage, e.g. datasets and models. MinIO is a high-performance, open-source object storage server designed for storing unstructured data, and has an APi compatible with S3.
- Seldon Core: Used to deploy ML models as Kubernetes-native REST/gRPC services. Seldon is a novel, yet widely used tool that offers out-of-the-box observability, ingress and mesh configuration, metrics and tracing, and chaining models to build complex inference graphs.

The diagram below shows how an ML professional can interact with the platform.

![image](diagram.png)

## Let's Build the Platform!
You can follow the instructions and code snippets or install each component by running `./deploy_<component>` and the ipython notebook in the datascience folder used for modelling.

Requirements
We will use minikube, but you can use any Kubernetes cluster you have access to. To follow the instructions make sure that you have minikube, helm and docker installed. Optionally psql and mc would be useful. Once you have them installed start your cluster
`minikube start`

---

### Tracking Server
#### Deploying postgres in minikube
From our root directory let's create a new folder 
mkdir postgres && cd postgres 
In this tutorial I will have different namespaces for each component, so to start with postgres run:
kubectl create ns postgres

Let's create a `.env` file with variables used for database authentication and set the variables to your terminal `source .env`:
```ini
DB_USER=mlflowuser
DB_PASSWORD=mlflowpassword
DB_NAME=mlflowdb
```

We can install postgres in our cluster using a helm chart from bitnami.
Add the bitnami repository and install the chart
```bash
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
```
This will create a postgres deployment which will run an inital script to create a database, a schema, and a user with the credentials we set in the `.env` file. You can omit the image.tag to use the latest version. If you want to further have personalise your postgres deployment, check the different values you can set in the bitnami chart.


If all goes well we will see a success message! Did it work though 😄 ?

We can check that by running:
- `helm list -n postgres` : we should be able to see the postgres release
- Furthermore, in a 2nd terminal: we can forward the port of the postgres service to our computer: `kubectl port-forward -n postgres svc/postgresql 5432` . Then in the first terminal execute: `PGPASSWORD="$DB_PASSWORD" psql -U $DB_USER -d $DB_NAME -h localhost`. You should be able to connect to the database. Type `\q` to exit. You can `Ctrl+C` to stop the port-forwarding.

Hooray! We have a Postgres deployment in our cluster! 🙌 

#### Deploying MinIO in minikube
Let's start with the folder and namespace, from the root of our project: 
```bash
mkdir minio && cd minio
kubectl create ns minio-system
```
Create a `.env` file with variables used for blob storage authentication and set the variables to your terminal `source .env`:
```ini
MINIO_USER=minioadmin
MINIO_PASSWORD=minioadmin
```
We will also use a helm chart to install MinIO.
Note that if you are going to use minio in a production environment, the recommended way is to use the operator instead.
Since the focus of this tutorial is the deployment of the ML tools, I will leave the customisation of the MinIO deployment to your needs 😊 . I do recommend creating a values.yaml file to customise the installation, this one for example, will create an initial storage bucket called models
```yaml
buckets:
 - name: models
   purge: false
   policy: public
```
Let's now add the chart and install it.
```bash
helm repo add minio https://helm.min.io/
helm upgrade --install minio minio/minio \
--set accessKey=${MINIO_USER} \
--set secretKey=${MINIO_PASSWORD} \
--values ./values.yaml \
--namespace minio-system
```
This will create a minio deployment which will set the authentication credentials to the variables we set in the `.env` file. 

Let's verify the installation:

- `helm list -n minio-system` should show the MinIO release.
- Port-forward the minio service in a new terminal: `kubectl port-forward -n minio-system svc/minio 8090:9000` In your browser go to http://localhost:8090/minio/login and see your buckets.
- Alternatively, if you installed `mc`, then in the first terminal run `mc config host add minio-seldon http://localhost:8090 $MINIO_USER $MINIO_PASSWORD`. You should be able to connect to the minio server, try it by running `mc ls minio-seldon` to list the buckets. You can now `Ctrl+C` to stop the port-forwarding.

Exciting! We now have a deployment for artefact storage! 🎉

#### Deploying MLFlow to minikube

As before, From the root project
```bash
mkdir mlflow && cd mlflow
kubectl create ns mlflow
```
Create a `.env` file and `source .env` . The variable `MLFLOW_S3_ENDPOINT_URL` refers to MinIO's host, and the `AWS_` variables authenticate it MLFlow. The variables prefixed with `DB_` authenticate the server against Postgres.
```ini
MLFLOW_S3_ENDPOINT_URL=http://minio.minio-system.svc.cluster.local:9000/
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
DB_HOST=postgresql.postgres.svc.cluster.local
DB_PORT=5432
DB_NAME=mlflowdb
DB_USER=mlflowuser
DB_PASSWORD=mlflowpassword
DB_CONN=postgresql://mlflowuser:mlflowpassword@postgresql.postgres.svc.cluster.local:5432/mlflowdb?options=-csearch_path%3Dmlflow
```
Note that since we are running everything in the same cluster we can access services using Kubernetes nomenclature `service-name.namespace.svc.cluster.local:port` .

To deploy our MLFlow server we will use a community supported helm chart. I encourage you to go over its code to fully understand it. There is no official chart yet, but discussions are happening! 
```bash
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
```
To verify that we have done everything correctly, we can:
In a second terminal: `kubectl port-forward svc/mlflow 5000`

Open localhost:5000 in your browser to see the MLFlow UI.

Now we can start using our MLFlow tracking server! 🥳

## Install the Seldon Operator and ML Models environment
Before we go ahead and train models let's finish the set up by installing the Seldon-Core Operator, which will allow us to use our models as Kubernetes deployments. Let's start with the folder structure
mkdir seldon && cd seldon
First we will create a namespace for our ML models to exist as microservices. Seldon loads the artefacts from a specified URI, the recommended way is using RClone which syncs files from different cloud providers, MinIO in our case. To do so we need to configure a secret. MinIO follows S3 conventions. If you opt for a different cloud provider, you can check the RClone docs to see how to configure it.
```bash
kubectl create ns ml-models
kubectl create secret generic seldon-init-container-secret \
  --from-literal=RCLONE_CONFIG_S3_ACCESS_KEY_ID=${MINIO_USER} \
  --from-literal=RCLONE_CONFIG_S3_SECRET_ACCESS_KEY=${MINIO_PASSWORD} \
  --from-literal=RCLONE_CONFIG_S3_ENDPOINT=http://minio.minio-system.svc.cluster.local:9000 \
  --from-literal=RCLONE_CONFIG_S3_ENV_AUTH=false \
  --from-literal=RCLONE_CONFIG_S3_PROVIDER=minio \
  --from-literal=RCLONE_CONFIG_S3_TYPE=s3 \
  --namespace ml-models
```
Now we can install the Seldon operator in our cluster using helm.
```bash
kubectl create ns seldon-system
helm upgrade - install seldon-core seldon-core-operator \
 --repo https://storage.googleapis.com/seldon-charts \
 --set usageMetrics.enabled=true \
 --namespace seldon-system \
 --set istio.enabled=false
```
Note that if you want to enable ingress controllers (which I won't cover in this guide) you can set istio.enabled or ambassador.enabled to true.
To verify that the Seldon operator was properly installed installation, run:
helm list -n seldon-system you should be able to see the Seldon release.
kubectl get crd -n seldon-system you should also see that there are new CRDs for Seldon deployments. These are custom resources that will allow us to deploy our ML models natively as Kubernetes objects.

Congratulations, if you made it this far you have finished setting your very own Kubernetes native ML-Platform!  🤩 Now let's use it!

## Let's Train Some Models!
We will train some models for wine quality prediction, using sklearn and XGBoost. We will deploy a model with each framework using Seldon's prepackaged servers for XGBboost and for MLFlow. A prepackaged server means that we pull an existing docker image that will serve our models, and we only need to provide an artifact URI, and comply with the requirements of the images. If you want to have a custom server, which means you are in charge of loading your model, defining its input, and building the image please refer to the custom inference documentation.
Let's start with a conda environment with python 3.8 (the latest version supported at the time of writing):
```
conda create -n mlflow-k8s python=3.8 mlflow xgboost jupyterlab
conda activate mlflow-k8s 
```

You can follow the [notebook](datascience/wine_experiment.ipynb) to train and deploy models.

## Integration with other services
If you are interested in building another microservice (like a frontend) that consumes our model, I present you a prototype that uses streamlit to quickly build a presentation layer and make requests to our model.
We need these few steps to deploy a frontend:

Build the image: 

` eval $(minikube docker-env)` to use minikube's docker environment, and

`docker build -t ml-streamlit` . 


Create a new namespace and apply the manifest:
```bash
kubectl create ns fe
kubectl apply -f fe_manifest.yaml - namespace=fe
```
Port-forward the application kubectl port-forward -n fe svc/frontend-service 8080.
Visit localhost:8080 and interact with the model.

## Limitations and future work
Some caveats and limitations of the current guide include:
- Postgres installation: a production-ready deployment needs to account for space allocation, high availability, and replicas. The approach of this guide serves as an initial step, but the configuration should be further customised.
- MinIO installation: the recommended way for a production set-up is using the Operator.
- Ingress controller: Both your MLFlow server as well as your models should be available for your data scientists, who might not have direct access to the cluster. Installing an ingress for the tracking server and some authentication gives access to the platform. Enabling Ambassador or Istio in your Seldon installation automatically creates an ingress for your models.
- Observability: Monitoring your models is as crucial as monitoring any other microservice. Seldon provides a way to do so by sending metrics to a Prometheus instance which can be connected to Grafana as well. This is a crucial topic in MLOps, which deserves its own article.
- Batch jobs: Our current platform is useful for online models. For batch processing jobs further work needs to be done. Seldon provides an easy way to integrate with KubeFlow, Argo, and other ML Pipeline tools.

Some interesting topics for the future include
- Inference graphs: A powerful tool of Seldon deployments is building complex inference graphs that permit chain, combine, and route models.
- Custom inference servers: Some models are not MLFlow compatible, or require beta/nightly versions of some packages, so using prepackaged servers is not enough. Building your own inference server gives you the power to fully specify how to load models, what to run, and how to serve.

## Resources
- Seldon-Core documentation: https://docs.pytest.org/en/7.2.x/
- MLFlow: https://mlflow.org/docs/latest/index.html
- MinIO: https://github.com/minio/minio/
- Postgres: https://www.postgresql.org/