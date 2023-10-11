# openshift-ai-github-app

This is the code for a GitHub app to automate project managment tasks for
OpenShift AI, leveraging GitHub Issues and Projects.

This app is currently under active development and is not yet running in
production.

## Supported Actions

This app is expected to be installed at a GitHub organization level.
When installed in this way, the app will do the following:

1. For any newly opened issue in any repository in the organization, add
   the issue to specified GitHub project(s). See notes below for
   configuration of which projects issues will be added to.

## Setup & Prerequisites

### GitHub App Key File

A TLS key file is required for the app to authenticate to the GitHub API.
This key was created during the GitHub app setup and is stored securely.

The path to this key file is passed as the value of the `APP_KEY_PATH`
environment variable.

### Config File

Runtime configuration for the app is passed in via a config file. The path
to the configuration file must be specified in the `CONFIG_FILE_PATH`
environment variable.

The contents of the configuration file should be as follows:

```
---
add_issues_to_project:
  project_ids: # IDs of projects that newly created issues should be added to
    - 1
    - 2
```