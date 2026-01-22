pipeline {
    agent any
    
    // Define your destination folder here
    environment {
        DEPLOY_DIR = '/opt/blog'
    }

    triggers {
        githubPush()
    }

    stages {
        stage('Prepare Deployment') {
            steps {
                script {
                    // 1. Create the .env file in the workspace first
                    // Use 'cp' or inject secrets as discussed before
                    sh 'cp .env.example .env'
                }
            }
        }

        stage('Sync to /opt/blog') {
            steps {
                script {
                    echo "Syncing files to ${DEPLOY_DIR}..."
                    
                    // Ensure the directory exists
                    sh "mkdir -p ${DEPLOY_DIR}"
                    
                    // Use rsync to copy files from Jenkins workspace to /opt/blog
                    // -a: archive mode (preserves permissions/times)
                    // -v: verbose
                    // --delete: remove files in destination that no longer exist in source
                    // --exclude '.git': We don't need the git history in the runtime folder
                    sh "rsync -av --delete --exclude '.git' . ${DEPLOY_DIR}"
                }
            }
        }

        stage('Deploy') {
            steps {
                // Change execution context to /opt/blog
                dir(env.DEPLOY_DIR) {
                    script {
                        echo 'Starting Docker Compose...'
                        // Run compose from within /opt/blog
                        sh 'docker compose up -d --build --remove-orphans'
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Deployed successfully to /opt/blog'
            sh 'docker image prune -f'
        }
        failure {
            echo 'Deployment failed.'
        }
    }
}