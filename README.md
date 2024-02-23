This is a collection to tools to manage various management aspects of an AWS Bakcup setup.

Current Items

1. EBS Size Calculator for Snapshots (By Steve Kinsman) - Works out approximate EBS snapshot sizes using the "EBS Direct APIs", available since Dec 2019, to get the number of blocks in a volume's oldest snapshot, and number of changed blocks between # each two snapshots.
2. EBS Snapshot Orphans Report (By Steve Kinsman) - Manages "Orphaned" EBS Snapshots, i.e ones whose volume is deleted, and aren't being managed by AWS Backup or Amazon Data Lifecycle Manager, and aren't linked to an AMI.
3. AWS Backup Recovery Point Nuke Tool - Tool to delete all RPs in every AWS Backup Vault in the region within an AWS Account (with options to filter)
4. AWS Backup Vault Lock Configuration Report - Tool to apply AWS Backup Vault lock configurations to existing unlocked Vaults
