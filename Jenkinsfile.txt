pipeline {
    agent any

    stages {

        stage('Test') {
            steps {
                bat 'python -m pytest || exit 1'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe" build -t my-ci-app .'
            }
        }

        stage('Run Container') {
            steps {
                bat '"C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe" run my-ci-app'
            }
        }
    }
}
