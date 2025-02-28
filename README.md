# AI-Opt-Out-policy

This Lambda function manages AI services opt-out policies in AWS Organizations, allowing you to control AI service data usage across your organization and specific accounts.

# What is included:

Create organization-wide AI opt-out policies
Configure account-specific opt-outs
List all AI opt-out policies
Get effective policies for specific accounts
Automatic unique policy name generation
Detailed error handling and logging

# Prereq:
AWS Organizations setup with all features enabled
IAM permissions for managing AI opt-out policies
Lambda execution role with appropriate permissions
Python 3.8 or later

Lambda IAM permission required:

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "organizations:CreatePolicy",
                "organizations:AttachPolicy",
                "organizations:ListPolicies",
                "organizations:ListRoots",
                "organizations:ListTargetsForPolicy",
                "organizations:DescribePolicy",
                "organizations:DescribeEffectivePolicy"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "organizations:PolicyType": "AISERVICES_OPT_OUT_POLICY"
                }
            }
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
