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

def cap_postp(r, output):
    # Check to see if "Save and add information" was pressed
    if r.tablename == "cap_alert":
        if request.post_vars.get("add_info", False):
            r.next = URL(c="cap", f="alert", args=[r.resource.lastid, "info"])

    if r.tablename == "cap_info" or r.component and r.component.tablename == "cap_info":
        if request.post_vars.get("add_file", False):
            r.next = URL(c="cap", f="info", args=[r.component.lastid, "info_resource"])

        if request.post_vars.get("add_area", False):
            r.next = URL(c="cap", f="info", args=[r.component.lastid, "info_area"])

    return output

# =============================================================================
def alert():

    response.s3.postp = cap_postp
    response.s3.scripts.append("/%s/static/scripts/S3/s3.cap.js" % request.application)
    response.s3.stylesheets.append("S3/cap.css")
    return s3db.cap_alert_controller()

def info():
    response.s3.postp = cap_postp
    response.s3.scripts.append("/%s/static/scripts/S3/s3.cap.js" % request.application)
    response.s3.stylesheets.append("S3/cap.css")
    return s3db.cap_info_controller()
