pipeline {
    agent any

    environment {
        BANDIT_IMAGE     = "meenal933/bandit"
        SPECIALITY_IMAGE = "meenal933/speciality"
        FRONTEND_IMAGE   = "meenal933/frontend"

        ANSIBLE_INVENTORY = "Ansible/hosts.ini"
        ANSIBLE_PLAYBOOK  = "Ansible/deploy.yml"

        KUBECONFIG = "/var/lib/jenkins/.kube/config"
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    }

    stages {

        stage('Checkout Code') {
            steps {
                echo "Code checked out."
            }
        }

        stage('Build Docker Images') {
            steps {
                script {
                    echo "Building Docker images..."
                    sh "/Applications/Docker.app/Contents/Resources/bin/docker build -t ${BANDIT_IMAGE}:latest ./main1"
                    sh "/Applications/Docker.app/Contents/Resources/bin/docker build -t ${SPECIALITY_IMAGE}:latest ./main2"
                    sh "/Applications/Docker.app/Contents/Resources/bin/docker build -t ${FRONTEND_IMAGE}:latest ."
                }
            }
        }

        stage('Push Docker Images to DockerHub') {
    steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials',
                                          usernameVariable: 'DOCKER_USER',
                                          passwordVariable: 'DOCKER_PASS')]) {
            sh '''
                echo "$DOCKER_PASS" | /Applications/Docker.app/Contents/Resources/bin/docker login -u "$DOCKER_USER" --password-stdin
                /Applications/Docker.app/Contents/Resources/bin/docker push meenal933/bandit:latest
                /Applications/Docker.app/Contents/Resources/bin/docker push meenal933/speciality:latest
                /Applications/Docker.app/Contents/Resources/bin/docker push meenal933/frontend:latest
            '''
        }
    }
}

        stage('Load Images into Minikube') {
            steps {
                sh """
                    /opt/homebrew/bin/minikube image load ${BANDIT_IMAGE}:latest
                    /opt/homebrew/bin/minikube image load ${SPECIALITY_IMAGE}:latest
                    /opt/homebrew/bin/minikube image load ${FRONTEND_IMAGE}:latest
                """
            }
        }

        stage('Deploy with Ansible') {
            steps {
                sh """
                ansible-playbook -i ${ANSIBLE_INVENTORY} ${ANSIBLE_PLAYBOOK} \
                    -e bandit_tag=latest \
                    -e speciality_tag=latest \
                    -e frontend_tag=latest
                """
            }
        }
    }

    post {
        success { echo "Deployment successful!" }
        failure { echo "Deployment failed. Check logs above." }
    }
}
