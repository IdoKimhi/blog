pipeline {
  agent any

  triggers {
    pollSCM('H/5 * * * *')
  }

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Deploy') {
      steps {
        sh 'docker compose up -d --build'
      }
    }
  }
}
