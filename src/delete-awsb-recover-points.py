# pylint: disable = C0103, R0902, W1203, C0301, C0413, W0718, W0719
"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import traceback
import argparse
import boto3
import boto3.session
from botocore.exceptions import ClientError

def delete_recovery_point(region, backup_vault_name, recovery_point_arn):
    """
    This function will delete the selected AWS Backup Recovery Point from the AWS Backup Vault in the region.
    """    
    backup_client = boto3.client('backup', region_name=region)
    try:
        backup_client.delete_recovery_point(BackupVaultName=backup_vault_name, RecoveryPointArn=recovery_point_arn)
        print(f'Delete complete for RecoveryPoint :{recovery_point_arn} from Vault : {backup_vault_name}')
    except (ClientError, Exception):  # pylint: disable = W0703
        var = traceback.format_exc()        
        print(f'Delete FAILED for RecoveryPoint :{recovery_point_arn} from Vault : {backup_vault_name} with error : {var}')           

def process_aws_backup_rp_nuke(region, backup_vault_name_to_process, output_only=True):
    """
    This function will process the delete request and will only perform an output only if selected so.
    """
    print(f"Listing all AWS Backup vaults in the region: {region}")
    backup_client = boto3.client('backup', region_name=region)
    all_backup_vaults= []
    try:
        response = backup_client.list_backup_vaults()
        all_backup_vaults = response["BackupVaultList"]
        while "NextToken" in response:
            response = backup_client.list_backup_vaults(NextToken=response["NextToken"])
            all_backup_vaults.extend(response["BackupVaultList"])
    except (ClientError, Exception):  # pylint: disable = W0703
        var = traceback.format_exc()        
        print(f'Processing FAILED for list_backup_vaults with error : {var}')  

    for backup_vault in all_backup_vaults:
        backup_vault_name = backup_vault['BackupVaultName']
        if backup_vault_name_to_process:
            if backup_vault_name_to_process.lower() != backup_vault_name.lower():
                print(f"Skipping processing Vault: {backup_vault_name} as it does NOT match : {backup_vault_name_to_process}")
                continue
        print(f"Processing Vault: {backup_vault_name}")
        recovery_points_list = []
        try:
            response = backup_client.list_recovery_points_by_backup_vault(BackupVaultName=backup_vault_name)
            recovery_points_list = response["RecoveryPoints"]
            while "NextToken" in response:
                response = backup_client.list_recovery_points_by_backup_vault(BackupVaultName=backup_vault_name,NextToken=response["NextToken"])
                recovery_points_list.extend(response["RecoveryPoints"])
        except (ClientError, Exception):  # pylint: disable = W0703
            var = traceback.format_exc()        
            print(f'Processing FAILED for list_recovery_points ({backup_vault_name})with error : {var}')      

        print(f"Processing {len(recovery_points_list)} recovery points from AWS Backup Vault : {backup_vault_name}")
        for recovery_point in recovery_points_list:
            recovery_point_arn = recovery_point['RecoveryPointArn']
            print(f'Processing delete of RecoveryPoint :{recovery_point_arn} from Vault : {backup_vault_name}')
            if not output_only:
                delete_recovery_point(region, backup_vault_name, recovery_point_arn)

if __name__ == "__main__":
    output_only = True
    parser = argparse.ArgumentParser(description='AWS Backup Recovery Point Nuke Tool')
    parser.add_argument('-v', '--vaultname', type=str, metavar='nameofvault', help='scope only on selected vault name')
    parser.add_argument('-d', '--delete', action='store_true', help='Delete the Recovery Point(s)')
    args = parser.parse_args()
    session_id = boto3.session.Session().client("sts").get_caller_identity()
    print(f'Starting script execution using identity : {session_id}')
    aws_account_id = boto3.client("sts").get_caller_identity()["Account"]
    aws_region_id = boto3.session.Session().region_name
    exe_env = f'Execution environment as AWS Account id  : {aws_account_id} in Region : {aws_region_id}. Type Y or Yes to continue.'
    print(f'Setting up {exe_env}')
    user_input = input("Please confirm " + exe_env + "\n")
    if user_input.lower() in ['true', '1', 't', 'y','yes']:
        if args.delete:
            output_only = False  # Set to True to only output what will be deleted without actually deleting
        process_aws_backup_rp_nuke(aws_region_id, args.vaultname,output_only)
    else:
        print(f'Skipping processing based on user input : {user_input}')
