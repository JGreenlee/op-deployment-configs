import boto3
from botocore.exceptions import ClientError
import os
import logging
import sys
import argparse

logger = logging.getLogger()
logger.setLevel(logging.INFO)
# If you don't have boto3 installed, make sure to `pip install boto3` before running this script.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Read and display Cognito user profiles from a specified user pool."
    )

    auth_group = parser.add_mutually_exclusive_group(required=True)
    auth_group.add_argument(
        '-l', '--local',
        action='store_true',
        help='Running locally. Reads AWS credentials from environment variables.'
    )
    auth_group.add_argument(
        '-g', '--github',
        action='store_true',
        help='Must be run on GitHub Actions.'
    )

    pool_group = parser.add_mutually_exclusive_group(required=True)
    pool_group.add_argument(
        '-p', '--pool-name',
        help='Full Cognito user pool name (e.g. nrelopenpath-prod-myprogram)'
    )
    pool_group.add_argument(
        '-c', '--config',
        help='Path to a config file; pool name will be derived as nrelopenpath-prod-<filename>'
    )

    args = parser.parse_args()

    if args.config:
        filepath_raw = args.config
        filename_raw = filepath_raw.split("/")[-1]
        filename = filename_raw.split('.')[0]
        pool_name = "nrelopenpath-prod-" + filename
    else:
        pool_name = args.pool_name

if args.local:
    ACCESS = os.environ.get("AWS_ACCESS_KEY_ID")
    SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY")
    TOKEN = os.environ.get("AWS_SESSION_TOKEN")
    AWS_REGION = "us-west-2"

    cognito_client = boto3.client(
        'cognito-idp',
        aws_access_key_id=ACCESS,
        aws_secret_access_key=SECRET,
        aws_session_token=TOKEN,
        region_name=AWS_REGION
    )

if args.github:
    AWS_REGION = os.environ.get("AWS_REGION")
    cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)


def read_userpool_obj_list_on_all_pages(cognito_client):
    # From https://stackoverflow.com/a/64698263
    response = cognito_client.list_user_pools(MaxResults=60)
    next_token = response.get("NextToken", None)
    print(f'Received response with {len(response["UserPools"])=} and {next_token=}')
    user_pool_obj_list = response["UserPools"]
    while next_token is not None:
        response = cognito_client.list_user_pools(NextToken=next_token, MaxResults=60)
        next_token = response.get("NextToken", None)
        print(f'Received response with {len(response["UserPools"])=} & {next_token=}')
        user_pool_obj_list.extend(response["UserPools"])
    return user_pool_obj_list


def get_userpool_id(pool_name, cognito_client):
    all_user_pools = read_userpool_obj_list_on_all_pages(cognito_client)
    pool_names = [user_pool["Name"] for user_pool in all_user_pools]
    if pool_name not in pool_names:
        return False, None
    pool_index = pool_names.index(pool_name)
    pool_id = all_user_pools[pool_index]["Id"]
    return True, pool_id


def get_all_users(pool_id, cognito_client):
    """List all users in the pool, handling pagination."""
    try:
        response = cognito_client.list_users(UserPoolId=pool_id)
        users = response["Users"]
        pagination_token = response.get("PaginationToken", None)
        while pagination_token is not None:
            response = cognito_client.list_users(
                UserPoolId=pool_id,
                PaginationToken=pagination_token
            )
            users.extend(response["Users"])
            pagination_token = response.get("PaginationToken", None)
        return users
    except ClientError as err:
        logger.error(
            "Couldn't list users for %s. Here's why: %s: %s",
            pool_id,
            err.response["Error"]["Code"],
            err.response["Error"]["Message"],
        )
        raise


def display_user(user):
    for key in sorted(user.keys()):
        print(f"  {key}: {user[key]}")
    print()


######################################################################
is_userpool_exist, pool_id = get_userpool_id(pool_name, cognito_client)

if not is_userpool_exist:
    print(f"{pool_name} does not exist. Check the pool name and try again.")
    sys.exit(1)

users = get_all_users(pool_id, cognito_client)
print(f"\nUser pool: {pool_name}  ({pool_id})")
print(f"Total users: {len(users)}\n")
print("-" * 60)

for user in users:
    display_user(user)
