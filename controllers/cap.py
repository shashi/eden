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

def cap_rest_controller():
    tablename = "%s_%s" % (module, resourcename)
    table = s3db[tablename]
    action = "default"

    #def prep(r):
    #    if r.method == "create" and \
    #       request.get_vars.standalone_form:
    #        if r.http == "GET":
    #            action = "json_form"
    #        elif r.http == "POST":
    #            action = "json_create"
    #    return True

    #response.s3.prep = prep

    response.s3.scripts.append("/%s/static/scripts/S3/s3.cap.js" % request.application)
    response.s3.stylesheets.append("S3/cap.css")

    if request.get_vars.standalone_form:
        output = str(SQLFORM(table))
        return output
    elif action == "json_create":
        # create new item and return json representation
        output = "{}"
    else:
        output = s3_rest_controller()
    return output

# =============================================================================
def alert():
    output = s3_rest_controller()
    return output
def info():
    return cap_rest_controller()
def info_resource():
    return cap_rest_controller()
def info_area():
    return cap_rest_controller()
