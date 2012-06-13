# -*- coding: utf-8 -*-

"""
    CAP Module - Controllers
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
    """ CAP Alerts RESTful controller """

    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]

    response.s3.scripts.append("/%s/static/scripts/S3/s3.cap.js" % request.application)
    response.s3.stylesheets.append("S3/cap.css")

    output = s3_rest_controller()
    return output
