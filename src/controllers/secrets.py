import base64
import logging
import os

import boto3

logger = logging.getLogger()


def get_secret(secret_name):
    # Used when running on developer machine
    if secret := os.getenv(secret_name):
        logger.info(f"Retrieving {secret_name} secret from env vars")
        return secret

    # Used when running inside docker-compose network
    if os.path.exists(f"/run/secrets/{secret_name}"):
        logger.info(f"Retrieving {secret_name} secret from secret file")
        with open(f"/run/secrets/{secret_name}") as sfile:
            return sfile.read()

    # Used when deployed to AWS
    logger.info(f"Retrieving {secret_name} secret from secret manager")
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name="eu-west-2"
    )

    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    logger.debug(f"Secret '{secret_name}' = {get_secret_value_response}")
    if 'SecretString' in get_secret_value_response:
        return get_secret_value_response['SecretString']
    else:
        return base64.b64decode(get_secret_value_response['SecretBinary'])
