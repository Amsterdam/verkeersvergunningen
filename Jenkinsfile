#!groovy
def PROJECT_NAME = "verkeersvergunningen"
def PLAYBOOK = 'deploy.yml'
def SLACK_CHANNEL = '#waarnemingen-deployments'
def SLACK_MESSAGE = [
    "title_link": BUILD_URL,
    "fields": [
        ["title": "Project","value": PROJECT_NAME],
        ["title":"Branch", "value": BRANCH_NAME, "short":true],
        ["title":"Build number", "value": BUILD_NUMBER, "short":true]
    ]
]


pipeline {
    agent any

    options {
        timeout(time: 1, unit: 'HOURS')
    }

    environment {
        SHORT_UUID = sh( script: "uuidgen | cut -d '-' -f1", returnStdout: true).trim()
        COMPOSE_PROJECT_NAME = "${PROJECT_NAME}-${env.SHORT_UUID}"
        VERSION = env.BRANCH_NAME.replace('/', '-').toLowerCase().replace(
            'main', 'latest'
        )
        IS_RELEASE = "${env.BRANCH_NAME ==~ "release/.*"}"
    }

    stages {
        stage('Test') {
            steps {
                sh 'make test'
            }
        }

        stage('Build') {
            steps {
                sh 'make build'
            }
        }

        stage('Push and deploy') {
            when {
                anyOf {
                    branch 'main'
                    buildingTag()
                    environment name: 'IS_RELEASE', value: 'true'
                }
            }
            stages {
                stage('Push') {
                    steps {
                        retry(3) {
                            sh 'make push'
                        }
                    }
                }

                stage('Deploy to acceptance') {
                    when {
                        branch 'main'
                    }
                    steps {
                        sh 'VERSION=acceptance make push'
                        build job: 'Subtask_Openstack_Playbook', parameters: [
                            string(name: 'PLAYBOOK', value: PLAYBOOK),
                            string(name: 'INVENTORY', value: "acceptance"),
                            string(
                                name: 'PLAYBOOKPARAMS',
                                value: "-e 'deployversion=${VERSION} cmdb_id=app_verkeersvergunningen'"
                            )
                        ], wait: true
                    }
                }

                stage('Deploy to production') {
                    when { buildingTag() }
                    steps {
                        sh 'VERSION=production make push'
                        build job: 'Subtask_Openstack_Playbook', parameters: [
                            string(name: 'PLAYBOOK', value: PLAYBOOK),
                            string(name: 'INVENTORY', value: "production"),
                            string(
                                name: 'PLAYBOOKPARAMS',
                                value: "-e 'deployversion=${VERSION} cmdb_id=app_verkeersvergunningen'"
                            )
                        ], wait: true
                    }
                }
            }
        }

    }
    post {
        always {
            sh 'make clean'
        }
        failure {
            slackSend(channel: SLACK_CHANNEL, attachments: [SLACK_MESSAGE <<
                [
                    "color": "#D53030",
                    "title": "Build failed :fire:",
                ]
            ])
        }
    }
}
