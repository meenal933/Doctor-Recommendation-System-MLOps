pipeline {
    agent any

    environment {
        BANDIT_IMAGE     = "meenal933/bandit"
        SPECIALITY_IMAGE = "meenal933/speciality"
        FRONTEND_IMAGE   = "meenal933/frontend"

        ANSIBLE_INVENTORY = "Ansible/hosts.ini"
        ANSIBLE_PLAYBOOK  = "Ansible/deploy.yml"

        KUBECONFIG = "/var/lib/jenkins/.kube/config"
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
                    sh 'docker build -t meenal933/bandit:latest ./main1'
        sh 'docker build -t meenal933/speciality:latest ./main2'
        sh 'docker build -t meenal933/frontend:latest .'
                }
            }
        }

        stage('Push Docker Images to DockerHub') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', 'dockerhub-credentials') {
                        sh "docker push ${BANDIT_IMAGE}:${BUILD_NUMBER}"
                        sh "docker push ${BANDIT_IMAGE}:latest"
                        sh "docker push ${SPECIALITY_IMAGE}:${BUILD_NUMBER}"
                        sh "docker push ${SPECIALITY_IMAGE}:latest"
                        sh "docker push ${FRONTEND_IMAGE}:${BUILD_NUMBER}"
                        sh "docker push ${FRONTEND_IMAGE}:latest"
                    }
                }
            }
        }

        stage('Load Images into Minikube') {
            steps {
                sh """
                    minikube image load ${BANDIT_IMAGE}:latest
                    minikube image load ${SPECIALITY_IMAGE}:latest
                    minikube image load ${FRONTEND_IMAGE}:latest
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
        success {
            echo "Deployment successful!"
        }
        failure {
            echo "Deployment failed. Check logs above."
        }
    }
}
