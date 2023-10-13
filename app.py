#! /usr/bin/env python3

import logging
import os
import requests
import sys
import traceback
import yaml

from flask import Flask, request
from github import Github, GithubIntegration

Log_Format = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(
    stream=sys.stdout,
    filemode="w",
    format=Log_Format
)


app = Flask(__name__)

app_id = '406193' # The unique GitHub App ID for the OpenShift AI Project Manager app
config_file_path = os.environ['CONFIG_FILE_PATH']

with open ('config.yaml') as config_file:
    config = yaml.safe_load(config_file.read())
    PROJECT_IDS = config['add_issues_to_project']['target_projects']

app_key = os.environ['GITHUB_APP_KEY']

# Create an GitHub integration instance
git_integration = GithubIntegration(
    app_id,
    app_key,
)

def get_project_node_id(token, project_id, organization_name):
    headers = {
        'Authorization': f'Bearer {token}'
    }

    query = 'query{organization(login: \"' + organization_name + '\") {projectV2(number: ' + project_id + '){id}}}'
    request = requests.post('https://api.github.com/graphql',
                            json={'query': query},
                            headers=headers)
    return request.json()['data']['organization']['projectV2']['id']
    
    

def add_issue_to_project(token, project_id, issue_id):
    headers = {
        'Authorization': f'Bearer {token}'
    }

    app.logger.info(f'Adding issue {issue_id} to project {project_id}')

    query = 'mutation {addProjectV2ItemById(input: {projectId: \"' + project_id + '\" contentId: \"' + issue_id + '\"}) {item {id}}}'
    result = requests.post('https://api.github.com/graphql',
                            json={'query': query},
                            headers=headers)
    if result.json().get('errors', []):
        app.logger.error(f'Failed to add issue to project: {result.json()}')
        return False
    return True


@app.route("/", methods=['POST'])
def bot():
    try:
        # Get the event payload
        payload = request.json

        # Check if the event is a GitHub issue creation event
        if not all(k in payload.keys() for k in ['action', 'issue', 'installation', 'organization']) and \
                payload['action'] == 'opened':
            return "Webhook event was not a newly opened issue"
        
        # Get the app installation ID and corresponding token so that we can add the issue to the project as the GitHub App persona
        installation_id = payload['installation']['id']
        token = git_integration.get_access_token(installation_id).token

        # Get the organization name for the issue that was created
        organization_name = payload['organization']['login']
        
        # Get the unique ID for the project we're targeting
        project_node_ids = []
        for target_project in PROJECT_IDS:
            project_org, project_id = target_project.split('/')
            project_node_ids.append(get_project_node_id(token, str(project_id), project_org))

        # Get the unique ID for the issue that was created
        issue_node_id = payload['issue']['node_id']

        for project in project_node_ids:
            add_issue_to_project(token, project, issue_node_id)

        return 'OK'
    except:
        app.logger.error(traceback.format_exc())
        return 'FAILED'


if __name__ == '__main__':
    debug_mode = True if os.environ.get('FLASK_DEBUG', '') else False
    app.run(debug=debug_mode, port=5000)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)