// Jenkinsfile

// 1. Define Agent and Global Environment Variables
pipeline {
    agent any 
    environment {
        // Infrastructure Details (Pulled from your Terraform setup)
        ECR_URI = '639811820283.dkr.ecr.ap-south-1.amazonaws.com/flask-ml-repo'
        K8S_PATH = 'k8s-manifests'
        AWS_REGION = 'ap-south-1'
        
        // Credentials IDs set up in the Jenkins Credentials Manager (Secret Text Kind)
        AWS_SECRET_KEY_ID = 'aws-secret-key-id'
        AWS_ACCESS_KEY_ID = 'aws-access-key-id'

        // Dynamic tag based on Git Commit ID (Ensures unique image for every build)
        IMAGE_TAG = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim() 
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo "Cloning source code from repository..."
                // Uses the GitHub PAT credential set in the SCM section of the Jenkins job config
                checkout scm 
            }
        }
        
        stage('Docker Build & Push to ECR') {
            steps {
                script {
                    // *** Securely retrieve both keys using the Secret Text Kind ***
                    withCredentials([
                        // Retrieve Secret Access Key
                        [
                            $class: 'SecretStringBinding', 
                            credentialsId: AWS_SECRET_KEY_ID, 
                            variable: 'AWS_SECRET_ACCESS_KEY' // Injects variable for the shell session
                        ],
                        // Retrieve Access Key ID
                        [
                            $class: 'SecretStringBinding', 
                            credentialsId: AWS_ACCESS_KEY_ID, 
                            variable: 'AWS_ACCESS_KEY_ID'
                        ]
                    ]) {
                        // Login to ECR: AWS CLI uses the injected environment variables automatically
                        sh 'aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}'
                        
                        // Build the new Docker image
                        sh "docker build -t ${ECR_URI}:${IMAGE_TAG} -f Dockerfile ."
                        
                        // Push the image to AWS ECR
                        sh "docker push ${ECR_URI}:${IMAGE_TAG}"
                        echo "Image pushed: ${ECR_URI}:${IMAGE_TAG}"
                    }
                }
            }
        }
        
        stage('Deploy to EKS') {
            steps {
                script {
                    // Update the deployment manifest with the new unique image tag
                    sh "sed -i 's|image:.*|image: ${ECR_URI}:${IMAGE_TAG}|g' ${K8S_PATH}/deployment.yaml"
                    
                    // Apply the updated deployment to the EKS cluster
                    sh "kubectl apply -f ${K8S_PATH}/deployment.yaml"
                    
                    // Apply the service (to maintain the NLB configuration)
                    sh "kubectl apply -f ${K8S_PATH}/service.yaml"
                }
            }
        }
        
        stage('Verify Rollout') {
            steps {
                // Wait for Kubernetes to confirm the new Pods are running before finishing the job
                sh 'kubectl rollout status deployment/ml-flask-deployment'
            }
        }
    }
}