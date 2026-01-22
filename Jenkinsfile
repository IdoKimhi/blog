pipeline {
  agent any

  environment {
    DEPLOY_HOST = '192.168.1.186'   // set to the server LAN IP
    DEPLOY_DIR  = '/opt/blog'
  }

  triggers { githubPush() }

  stages {
    stage('Checkout') { steps { checkout scm } }

    stage('Prepare .env') {
      steps {
        sh 'cp .env.example .env'
        // later replace with a Jenkins Secret file if you want
      }
    }

    stage('Sync to server') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'deploy-ssh', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
          sh '''
            set -e
            tar --exclude=.git -C "$WORKSPACE" -cf - . | \
              ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new "$SSH_USER@$DEPLOY_HOST" \
              "mkdir -p '$DEPLOY_DIR' && tar -xf - -C '$DEPLOY_DIR'"
          '''
        }
      }
    }

    stage('Deploy on server') {
      steps {
        withCredentials([sshUserPrivateKey(credentialsId: 'deploy-ssh', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')]) {
          sh '''
            set -e
            ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new "$SSH_USER@$DEPLOY_HOST" \
              "cd '$DEPLOY_DIR' && docker compose up -d --build --remove-orphans"
          '''
        }
      }
    }
  }
}
