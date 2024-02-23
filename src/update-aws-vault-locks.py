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

import argparse
import sys
import traceback
import boto3
from botocore.exceptions import ClientError


update_confirmed = False

parser = argparse.ArgumentParser(description='AWS Backup Vault Lock Configuration Report')
parser.add_argument('-m', '--min-retention', type=int, metavar='n', help='The Backup Vault Lock configuration that specifies the minimum retention period that the vault retains its recovery points.')
parser.add_argument('-x', '--max-retention', type=int, metavar='n', help='The Backup Vault Lock configuration that specifies the maximum retention period that the vault retains its recovery points.')
parser.add_argument('-c', '--changeable-for', type=int, metavar='n', help='The Backup Vault Lock configuration that specifies the number of days before the lock date.')
parser.add_argument('-v', '--vaultname', type=str, metavar='nameofvault', help='scope only on selected vault name')
parser.add_argument('-a', '--apply', action='store_true', help='Apply AWS Backup Vault Lock instead of just reporting them')
args = parser.parse_args()

if not (args.min_retention or args.min_retention or args.changeable_for):
    parser.print_help(sys.stderr)
    sys.exit()

session_id = boto3.session.Session().client("sts").get_caller_identity()
aws_account_id = boto3.client("sts").get_caller_identity()["Account"]
aws_region_id = boto3.session.Session().region_name
exe_env = f'Execution environment as AWS Account id  : {aws_account_id} in Region : {aws_region_id}. Type Y or Yes to continue.'
user_input = input("Please confirm " + exe_env + "\n")
#A Security check to ensure you are NOT running this in an unintended region and account combination
backup_client = boto3.client('backup', region_name=aws_region_id)
if user_input.lower() in ['true', '1', 't', 'y','yes']:
    print(f"Listing all AWS Backup vaults in the region: {aws_region_id}")
    backup_client = boto3.client('backup', region_name=aws_region_id)
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
        if args.vaultname:
            if args.vaultname.lower() != backup_vault_name.lower():
                print(f"Skipping processing Vault: {backup_vault_name} as it does NOT match : {args.vaultname}")
                continue
        print(f"Processing Vault: {backup_vault_name}")
        response = backup_client.describe_backup_vault(BackupVaultName=backup_vault_name,BackupVaultAccountId=aws_account_id)
        vault_locked = response.get('Locked')
        if not vault_locked:
            try:
                print(f'Vault :{backup_vault_name} NOT Locked.')
                if args.apply:
                    if not update_confirmed:
                        print("You have chosen to update matching AWS Backup Vaults.  It's recommended that you first run this "
                                "script without the '--apply' option to get a report of AWS Backup Vaults that will be updated.\n"
                                "Are you sure you want to continue (Y/N)?: ", end=''
                        )
                        response = input()
                        if response.lower() in ['true', '1', 't', 'y','yes']:
                            update_confirmed = True
                        else:
                            sys.exit()
                    print(f'Vault :{backup_vault_name} NOT Locked. Applying Vault Lock Configuration between : {args.min_retention} and {args.max_retention} for : {args.changeable_for} Days')
                    backup_client.put_backup_vault_lock_configuration(
                        BackupVaultName=backup_vault_name,
                        MinRetentionDays=args.min_retention,
                        MaxRetentionDays=args.max_retention,
                        ChangeableForDays=args.changeable_for
                    )        
                    print(f'VaultLock configuration updated for Vault :{backup_vault_name}')
            except (ClientError, Exception):  # pylint: disable = W0703
                var = traceback.format_exc()        
                print(f'Updated FAILED for Vault :{backup_vault_name} with error : {var}')
        else:
            min_retention = response.get('MinRetentionDays')
            max_retention = response.get('MaxRetentionDays')
            lock_date = response.get('LockDate')
            print(f"Vault: {backup_vault_name} already locked on {lock_date} with Min as : {min_retention} and Max as : {max_retention}")
