import boto3
import json
import os
from botocore.exceptions import ClientError
from datetime import datetime

def get_policy_by_name(org_client, policy_name):
    """Helper function to find AI opt-out policy by name"""
    try:
        paginator = org_client.get_paginator('list_policies')
        matching_policies = []
        for page in paginator.paginate(Filter='AISERVICES_OPT_OUT_POLICY'):
            for policy in page.get('Policies', []):
                if policy.get('Name', '').startswith(policy_name):
                    matching_policies.append(policy)
        return matching_policies
    except ClientError as e:
        print(f"Error finding AI opt-out policy: {str(e)}")
        return []

def generate_unique_policy_name(org_client, base_name):
    """Generate a unique policy name by adding timestamp if base name exists"""
    existing_policies = get_policy_by_name(org_client, base_name)
    if not existing_policies:
        return base_name
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{base_name}-{timestamp}"

def update_or_create_policy(org_client, policy_name, policy_content, description, target_id=None):
    """Helper function to update existing AI opt-out policy or create new one"""
    try:
        unique_policy_name = generate_unique_policy_name(org_client, policy_name)
        
        response = org_client.create_policy(
            Content=json.dumps(policy_content),
            Description=description,
            Name=unique_policy_name,
            Type='AISERVICES_OPT_OUT_POLICY'
        )
        
        policy_id = response.get('Policy', {}).get('PolicyId')
        if policy_id and target_id:
            org_client.attach_policy(
                PolicyId=policy_id,
                TargetId=target_id
            )
        return policy_id, unique_policy_name
            
    except ClientError as e:
        print(f"Error in update_or_create_policy: {str(e)}")
        raise

def create_account_opt_out_policy(org_client, account_id, services_to_opt_out=None):
    """Create an account-specific opt-out policy"""
    if services_to_opt_out is None:
        services_to_opt_out = ["default"]  # Opt out of all services by default

    policy_content = {
        "services": {
            "default": {
                "opt_out_policy": {
                    "@@assign": "optIn"  # Override organization default
                }
            }
        }
    }

    # Add specific service opt-outs
    for service in services_to_opt_out:
        policy_content["services"][service] = {
            "opt_out_policy": {
                "@@assign": "optOut"
            }
        }

    policy_name = f"AI-OptOut-Account-{account_id}"
    description = f"Account-specific AI opt-out policy for {account_id}"

    return update_or_create_policy(
        org_client,
        policy_name,
        policy_content,
        description,
        account_id
    )

def create_ai_optout_policies(event_details=None):
    """Create organization and account level AI opt-out policies"""
    org_client = boto3.client('organizations')
    
    account_id = os.environ.get('TARGET_ACCOUNT_ID')
    if not account_id:
        raise ValueError("TARGET_ACCOUNT_ID environment variable is not set")

    # Organization-level AI opt-out policy
    org_policy = {
        "services": {
            "default": {
                "opt_out_policy": {
                    "@@assign": "optOut"
                }
            }
        }
    }

    try:
        results = {}

        # Get organization root ID
        roots = org_client.list_roots()['Roots']
        if not roots:
            raise ValueError("No roots found in the organization")
        root_id = roots[0]['Id']

        # Create organization-level policy
        org_policy_id, org_policy_name = update_or_create_policy(
            org_client,
            'AI-OptOut-Org-Policy',
            org_policy,
            'Organization-wide AI opt-out policy',
            root_id
        )
        results['org_policy'] = {
            'id': org_policy_id,
            'name': org_policy_name
        }

        # Handle account-specific opt-outs if provided
        if event_details and 'account_opt_outs' in event_details:
            results['account_opt_outs'] = []
            for account_config in event_details['account_opt_outs']:
                account_id = account_config.get('account_id')
                services = account_config.get('services', ['default'])
                
                if account_id:
                    policy_id, policy_name = create_account_opt_out_policy(
                        org_client,
                        account_id,
                        services
                    )
                    results['account_opt_outs'].append({
                        'account_id': account_id,
                        'policy_id': policy_id,
                        'policy_name': policy_name,
                        'services': services
                    })

        return {
            'statusCode': 200,
            'body': json.dumps(results)
        }
        
    except Exception as e:
        error_message = f"Error creating policies: {str(e)}"
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_message
            })
        }

def list_ai_policies():
    """List all AI opt-out policies"""
    try:
        org_client = boto3.client('organizations')
        policies_list = []
        
        paginator = org_client.get_paginator('list_policies')
        for page in paginator.paginate(Filter='AISERVICES_OPT_OUT_POLICY'):
            for policy in page.get('Policies', []):
                try:
                    policy_detail = org_client.describe_policy(PolicyId=policy.get('Id'))
                    policy_content = policy_detail.get('Policy', {}).get('Content', '{}')
                    
                    targets = []
                    target_paginator = org_client.get_paginator('list_targets_for_policy')
                    for target_page in target_paginator.paginate(PolicyId=policy.get('Id')):
                        targets.extend(target_page.get('Targets', []))
                    
                    policies_list.append({
                        'Name': policy.get('Name'),
                        'Id': policy.get('Id'),
                        'Content': json.loads(policy_content),
                        'Targets': targets
                    })
                except ClientError as e:
                    print(f"Error getting policy details: {str(e)}")
                    continue
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'policies': policies_list
            })
        }
                
    except ClientError as e:
        error_message = f"Error listing policies: {str(e)}"
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_message
            })
        }

def get_effective_policy(account_id):
    """Get effective AI opt-out policy for an account"""
    try:
        org_client = boto3.client('organizations')
        
        response = org_client.describe_effective_policy(
            PolicyType='AISERVICES_OPT_OUT_POLICY',
            TargetId=account_id
        )
        
        policy_content = response.get('EffectivePolicy', {}).get('PolicyContent', '{}')
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'accountId': account_id,
                'effectivePolicy': json.loads(policy_content)
            })
        }
        
    except ClientError as e:
        error_message = f"Error getting effective policy: {str(e)}"
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_message
            })
        }

def lambda_handler(event, context):
    """Main Lambda handler for AI opt-out policy management"""
    try:
        action = event.get('action', 'create')
        
        if action == 'create':
            return create_ai_optout_policies(event.get('details'))
        elif action == 'list':
            return list_ai_policies()
        elif action == 'get_effective':
            account_id = event.get('account_id') or os.environ.get('TARGET_ACCOUNT_ID')
            if not account_id:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'error': 'account_id is required'
                    })
                }
            return get_effective_policy(account_id)
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Invalid action: {action}'
                })
            }
        
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_message
            })
        }
