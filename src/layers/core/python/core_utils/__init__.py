# -*- coding: utf-8 -*-
__all__ = [
    "datetime",
    "environment",
    "regex",
    "utils",
    "load_environment_variables",
    "enum"
]

import os


def load_environment_variables():
    try:
        from dotenv import load_dotenv
    except ImportError:
        pass
    else:
        if os.getenv("DEVELOPER") == "DeployUnittest":
            load_dotenv("./.env", override=False)
        load_dotenv()


load_environment_variables()
