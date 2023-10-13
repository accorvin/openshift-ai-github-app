# openshift-ai-project-manager

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

The contents of this key file must be passed as the value of the `GITHUB_APP_KEY`
environment variable.

### Config File

Runtime configuration for the app is passed in via a config file. The path
to the configuration file must be specified in the `CONFIG_FILE_PATH`
environment variable.

The config file used in production can be found at [config.yaml][config.yaml]
and it is copied into place during the app build process.

## Production Deployment

This GitHub app runs as an deployment on AWS App Runner. We use an AWS
CloudFormation template to automate this deployment.

### AppRunner GitHub Connection

AppRunner must authenticate to GitHub to pull the source code. A connection
was previously set up following the instructions
[here](https://docs.aws.amazon.com/apprunner/latest/dg/manage-connections.html)

The ARN for this connection is specified in the AppRunner's `AuthenticationConfiguration`
in [aws_deployment_template.yaml][aws_deployment_template.yaml]

### AWS Secret Creation

The GitHub App key file that is required for the app to authenticate to the
GitHub API is stored securely using AWS Secrets Manager. The following
command was used to create the secret: (this requires the [AWS CLI][awscli])

```
aws secretsmanager create-secret \
  --name openshift-ai-project-manager-github-app-key \
  --description "TLS key for the openshift-ai-project-manager GitHub app to authenticate to the GitHub API" \
  --secret-string file://PATH_TO_KEY_FILE.pem
```

### AppRunner Instance Role

Becuase the AppRunner service instance will reference the above AWS secret, the
instance needs to run with an AWS IAM role that allows it to connect to the secret.

Run the folowing command to create the role: (this requires the [AWS CLI][awscli])
(note that you will need to find the ARN for the secret that was created in the
above step and substitute it into the command as the value for `$SECRET_ARN`
in the `policy.json` file)

```
cat <<EOF > role-trust-relationship.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "tasks.apprunner.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

cat <<EOF > policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "$SECRET_ARN"
      ]
    }
  ]
}
EOF

aws iam create-role \
  --role-name openshift-ai-project-manager-github-app \
  --assume-role-policy-document file://role-trust-relationship.json

aws iam put-role-policy \
  --role-name openshift-ai-project-manager-github-app \
  --policy-name read-github-key \
  --policy-document file://policy.json

rm policy.json
rm role-trust-relationship.json
```

The role will be created and included in the output will be the ARN for the
created IAM role. Specify this ARN as the value of `InstanceRoleArn` in
[aws_deployment_demplate.yaml][aws_deployment_template.yaml].

### Stack Creation

Use the [cloudformation][cloudformation] tool to create the stack, uploading
[aws_deployment_template.yaml][aws_deployment_template.yaml] as the template
file.

[awscli]: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
[cloudformation]: https://console.aws.amazon.com/cloudformation/