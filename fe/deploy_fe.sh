docker build -t ml-streamlit .
kubectl create ns fe
kubectl apply -f fe_manifest.yaml --namespace=fe