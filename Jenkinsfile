// Jenkinsfile

// 1. Define Agent and Global Environment Variables
pipeline {
    agent any 
    environment {
        // Infrastructure Details (Confirmed ECR URI and Region)
        ECR_URI = '639811820283.dkr.ecr.ap-south-1.amazonaws.com/flask-ml-repo'
        K8S_PATH = 'k8s-manifests'
        AWS_REGION = 'ap-south-1'
        
        // Credential IDs set up in the Jenkins Credentials Manager (Secret Text Kind)
        // NOTE: These IDs MUST match the IDs you used when storing the keys in Jenkins.
        AWS_SECRET_KEY_ID = 'aws-secret-key-id' 
        AWS_ACCESS_KEY_ID = 'aws-access-key-id'

        // Dynamic tag generation
        IMAGE_TAG = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim() 
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo "Cloning source code from repository..."
                // Uses GitHub PAT credential set in the job configuration
                checkout scm 
            }
        }
        
        stage('Docker Build & Push to ECR') {
            steps {
                script {
                    // SECURE STEP: Binds the stored Secret Text values to environment variables.
                    withCredentials([
                        // Binds the Secret Access Key
                        secretText(credentialsId: AWS_SECRET_KEY_ID, variable: 'AWS_SECRET_ACCESS_KEY'),
                        // Binds the Access Key ID
                        secretText(credentialsId: AWS_ACCESS_KEY_ID, variable: 'AWS_ACCESS_KEY_ID')
                    ]) {
                        // 1. Authenticate Docker to ECR using the injected environment variables
                        sh 'aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}'
                        
                        // 2. Build the new Docker image
                        sh "docker build -t ${ECR_URI}:${IMAGE_TAG} -f Dockerfile ."
                        
                        // 3. Push the image to AWS ECR
                        sh "docker push ${ECR_URI}:${IMAGE_TAG}"
                        echo "Image pushed: ${ECR_URI}:${IMAGE_TAG}"
                    }
                }
            }
        }
        
        stage('Deploy to EKS') {
            steps {
                script {
                    // 1. Update the deployment manifest with the new unique image tag
                    sh "sed -i 's|image:.*|image: ${ECR_URI}:${IMAGE_TAG}|g' ${K8S_PATH}/deployment.yaml"
                    
                    // 2. Apply the updated deployment and service to the EKS cluster
                    sh "kubectl apply -f ${K8S_PATH}/deployment.yaml"
                    sh "kubectl apply -f ${K8S_PATH}/service.yaml"
                }
            }
        }
        
        stage('Verify Rollout') {
            steps {
                // Wait for Kubernetes to confirm the new Pods are running
                sh 'kubectl rollout status deployment/ml-flask-deployment'
                echo "Deployment successfully rolled out and updated on EKS."
            }
        }
    }
}