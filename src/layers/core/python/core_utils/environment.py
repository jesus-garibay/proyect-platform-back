# -*- coding: utf-8 -*-
"""
This module contains the Environment class.
"""
import os

ENVIRONMENT = os.environ.get("ENVIRONMENT")
DEVELOPER = os.environ.get("DEVELOPER")
LAMBDA_NAME = os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
URL_OAUTH = os.environ.get("URL_OAUTH")
SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWD = os.environ.get("SMTP_PASSWD")
SMTP = os.environ.get("SMTP")
COGNITOID = os.environ.get("COGNITO_USER_CLIENT_ID")
POOLID = os.environ.get("POOL_ID")
URL_RECOVERY = os.environ.get("URL_RECOVERY")
