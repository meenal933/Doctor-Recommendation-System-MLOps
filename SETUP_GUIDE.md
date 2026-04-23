# CareCompass (Sunny's Project) — Full Setup Guide for Mac
## Docker username: meenal933

---

## PHASE 1 — Install Prerequisites (Do this once)

```bash
# 1. Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Docker Desktop
brew install --cask docker
# → Open Docker Desktop from Applications and wait until it says "Running"

# 3. Install Minikube + kubectl
brew install minikube
brew install kubectl

# 4. Install Ansible
brew install ansible

# 5. Install Jenkins
brew install jenkins-lts
brew services start jenkins-lts
# → Jenkins runs at http://localhost:8080
```

---

## PHASE 2 — Prepare the Project

```bash
# Unzip Sunny's project
cd ~/Documents
unzip MLOps-Driven-Doctor-Recommendation-System-main.zip
cd MLOps-Driven-Doctor-Recommendation-System-main
```

### Copy the provided files into the project:
Copy these folders/files (provided alongside this guide) into the project root:
- `Ansible/`           → Ansible/hosts.ini, Ansible/deploy.yml
- `Kubernetes/`        → all .yaml.j2 files + logging/
- `Jenkinsfile`
- `app.py`             → REPLACE the existing app.py
- `Dockerfile`         → REPLACE the existing Dockerfile (if any) at root
- `requirements.txt`   → REPLACE root requirements.txt

---

## PHASE 3 — Build & Push Docker Images

```bash
# Login to Docker Hub with your credentials (meenal933)
docker login
# Enter username: meenal933
# Enter your Docker Hub password

# Build bandit service image
docker build -t meenal933/bandit:latest ./main1

# Build speciality service image
docker build -t meenal933/speciality:latest ./main2

# Build frontend image
docker build -t meenal933/frontend:latest .

# Push all images to Docker Hub
docker push meenal933/bandit:latest
docker push meenal933/speciality:latest
docker push meenal933/frontend:latest
```

> NOTE: main2 (speciality) has a large ML model (BioDistillGPT2) — the build will take 5-10 minutes.

---

## PHASE 4 — Start Minikube

```bash
# Start Minikube (make sure Docker Desktop is running first)
minikube start --driver=docker --memory=6144 --cpus=4

# Verify it's running
kubectl get nodes
# You should see: minikube   Ready
```

> Use 6GB memory because Sunny's speciality service loads a large ML model (transformers + torch).

---

## PHASE 5 — Load Images into Minikube

```bash
# Load all images into Minikube's internal Docker
# (Minikube cannot see your Mac's Docker images directly)
minikube image load meenal933/bandit:latest
minikube image load meenal933/speciality:latest
minikube image load meenal933/frontend:latest

# Verify images are loaded
minikube image ls | grep meenal933
```

---

## PHASE 6 — Deploy with Ansible

```bash
# From inside the project root
ansible-playbook -i Ansible/hosts.ini Ansible/deploy.yml \
  -e bandit_tag=latest \
  -e speciality_tag=latest \
  -e frontend_tag=latest
```

---

## PHASE 7 — Verify Deployment

```bash
# Check all pods (speciality may take 2-3 min to become Ready due to ML model loading)
kubectl get pods -w

# All 3 should show 1/1 Running:
# bandit-deployment-xxx      1/1   Running
# speciality-deployment-xxx  1/1   Running
# frontend-deployment-xxx    1/1   Running

# Get the frontend URL
minikube service frontend --url

# Open that URL in your browser
```

---

## PHASE 8 — Setup ELK Stack (Centralized Logging)

```bash
# Create logging namespace
kubectl create namespace logging

# Deploy Elasticsearch
kubectl apply -f Kubernetes/logging/elasticsearch.yaml
kubectl get pods -n logging   # wait until Running

# Deploy Kibana
kubectl apply -f Kubernetes/logging/kibana.yaml
kubectl get pods -n logging   # wait until Running

# Download and configure Filebeat
curl -O https://raw.githubusercontent.com/elastic/beats/7.17/deploy/kubernetes/filebeat-kubernetes.yaml

# Edit filebeat output to point to your elasticsearch
sed -i '' 's|elasticsearch:9200|elasticsearch.logging.svc.cluster.local:9200|g' filebeat-kubernetes.yaml

# Deploy Filebeat
kubectl apply -f filebeat-kubernetes.yaml

# Get Kibana URL
minikube service kibana -n logging --url
# Open in browser → Explore on my own → Stack Management → Index Patterns
# Create pattern: filebeat-*  → time field: @timestamp → Go to Discover
```

---

## PHASE 9 — Configure Jenkins (CI/CD)

```bash
# Get Jenkins initial password
cat ~/.jenkins/secrets/initialAdminPassword

# Open http://localhost:8080
# Paste password → Install suggested plugins
# Install extra plugins: Docker Pipeline, GitHub Integration, Ansible

# Copy kubeconfig for Jenkins
sudo mkdir -p /var/lib/jenkins/.kube
sudo cp ~/.kube/config /var/lib/jenkins/.kube/config
sudo chown -R $(whoami) /var/lib/jenkins/.kube

# Make tools available to Jenkins
sudo ln -sf $(which docker) /usr/local/bin/docker
sudo ln -sf $(which kubectl) /usr/local/bin/kubectl
sudo ln -sf $(which ansible-playbook) /usr/local/bin/ansible-playbook
```

### In Jenkins UI:
1. **Add Docker Hub credential:**
   - Manage Jenkins → Credentials → Global → Add Credential
   - Kind: Username with password
   - Username: `meenal933`
   - Password: your Docker Hub password
   - ID: `dockerhub-credentials`

2. **Create Pipeline job:**
   - New Item → Pipeline → name: `CareCompass-Sunny`
   - Pipeline Definition: `Pipeline script from SCM`
   - SCM: Git
   - Repository URL: your GitHub repo URL (push the project to GitHub first)
   - Branch: `main`
   - Script Path: `Jenkinsfile`
   - Save → Build Now

---

## Cleanup (when done)

```bash
kubectl delete deployment bandit-deployment speciality-deployment frontend-deployment
kubectl delete namespace logging
minikube stop
brew services stop jenkins-lts
```

---

## Quick Reference — All Service URLs

| Service       | How to get URL                            |
|---------------|-------------------------------------------|
| Frontend App  | `minikube service frontend --url`         |
| Kibana (ELK)  | `minikube service kibana -n logging --url`|
| Jenkins       | http://localhost:8080                     |
| Bandit API    | frontend-url + port 8000 + /docs          |

---

## Troubleshooting

**Speciality pod keeps restarting?**
```bash
kubectl logs deployment/speciality-deployment
# If model loading error → pod needs more time, increase initialDelaySeconds
# The ML model (BioDistillGPT2) takes ~60s to load
```

**ImagePullBackOff error?**
```bash
# Re-load images into minikube
minikube image load meenal933/speciality:latest
```

**Connection refused in browser?**
```bash
# Check all pods are 1/1 Running
kubectl get pods
# If speciality is 0/1, wait 2-3 more minutes for model to load
```
