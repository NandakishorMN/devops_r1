// Jenkinsfile

// 1. Define Agent and Global Environment Variables
pipeline {
    agent any 
    environment {
        // Infrastructure Details (Confirmed ECR URI and Region)
        ECR_URI = '639811820283.dkr.ecr.ap-south-1.amazonaws.com/flask-ml-repo'
        K8S_PATH = 'k8s-manifests'
        AWS_REGION = 'ap-south-1'
        
        // Credential ID set up in the Jenkins Credentials Manager as 'Username with password'
        // This ID MUST match the one you set in the Jenkins UI: nanda-dev-aws-up
        AWS_UP_CRED_ID = 'nanda-dev-aws-up' 

        // Dynamic tag generation (Ensures a unique image for every build)
        IMAGE_TAG = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim() 
    }

    stages {
        stage('Checkout Code') {
            steps {
                echo "Cloning source code from repository..."
                // Uses the GitHub PAT credential set in the job SCM section
                checkout scm 
            }
        }
        
        stage('Docker Build & Push to ECR') {
            steps {
                script {
                    // *** GUARANTEED FIX: Binds the Username/Password credential to variables ***
                    withCredentials([
                        // Kind: Username with password (Username=Access Key, Password=Secret Key)
                        usernamePassword(credentialsId: AWS_UP_CRED_ID, 
                                         usernameVariable: 'AWS_ACCESS_KEY_ID', // Injected variable name for Access Key
                                         passwordVariable: 'AWS_SECRET_ACCESS_KEY') // Injected variable name for Secret Key
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
                    // Kubectl automatically uses the kubeconfig file we copied to the Jenkins home directory
                    sh "kubectl apply -f ${K8S_PATH}/deployment.yaml"
                    sh "kubectl apply -f ${K8S_PATH}/service.yaml"
                }
            }
        }
        
        stage('Verify Rollout') {
            steps {
                // Wait for Kubernetes to confirm the new Pods are running and service is stable
                sh 'kubectl rollout status deployment/ml-flask-deployment'
                echo "Deployment successfully rolled out and updated on EKS."
            }
        }
    }
}