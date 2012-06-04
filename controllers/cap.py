# -*- coding: utf-8 -*-

"""
    Messaging Module - Controllers
"""

module = request.controller
resourcename = request.function

if module not in deployment_settings.modules:
    raise HTTP(404, body="Module disabled: %s" % module)

# -----------------------------------------------------------------------------
def index():
    """ Module's Home Page """

    module_name = deployment_settings.modules[module].name_nice
    response.title = module_name
    return dict(module_name=module_name)


# =============================================================================
def alert():
    """ Compose a Message which can be sent to a pentity via a number of different communications channels """

    return s3_rest_controller()

# =============================================================================
def create():
    return {}
