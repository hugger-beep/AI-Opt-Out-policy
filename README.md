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


# Lambda IAM permission required:

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

# The Code 
# Functions Overview:
## Main Components:

1. get_policy_by_name: Find existing policies

2. generate_unique_policy_name: Create unique policy names

3. update_or_create_policy: Create or update policies

4. create_account_opt_out_policy: Configure account-specific opt-outs

5. create_ai_optout_policies: Create organization and account policies

6. list_ai_policies: List all AI opt-out policies

7. get_effective_policy: Get effective policies for accounts
   
9. Error handling - Handles missing env variables, Invalid actions,  API errors, Permission Issues

# Add the following:
1. Appropriate timeout around 3-4 minutes
   
2. Enable AWS Lambda logging
   
3. Use Least privilege permission for your AWS Lambda
   
4. Test against non production accounts

