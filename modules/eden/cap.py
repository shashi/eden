# -*- coding: utf-8 -*-

""" Sahana Eden Messaging Model

    @copyright: 2009-2012 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ["S3CAPModel"]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3CAPModel(S3Model):
    """
        CAP: Common Alerting Protocol
        - this module is a non-functional stub

        http://eden.sahanafoundation.org/wiki/BluePrint/Messaging#CAP
    """

    names = ["msg_report",
             "cap_info_resource",
             "cap_info_area",
             "cap_info",
             "cap_alert"]

    def model(self):

        T = current.T
        s3 = current.response.s3

        location_id = self.gis_location_id
        message_id = self.msg_message_id

        tablename = "msg_report"
        table = self.define_table(tablename,
                                  message_id(),
                                  location_id(),
                                  Field("image", "upload", autodelete = True),
                                  Field("url", requires=IS_NULL_OR(IS_URL())),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        tablename = "cap_info_resource"
        table = self.define_table(tablename, 
                                  Field("resource_desc", required=True),
                                  Field("mime_type", notnull=True),
                                  Field("size", "integer"),
                                  Field("uri"), # needs a special validation
                                  Field("file", "upload"),
                                  # XXX: Should this be made per-info instead of per-file?
                                  Field("base64encode", "boolean"),
                                  #Field("deref_uri", "text"), <-- base 64 encoded
                                  Field("digest"),
                                  *s3.meta_fields())


        table.resource_desc.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The type and content of the resource file"),
                  T("The human-readable text describing the type and content, such as 'map' or 'photo', of the resource file.")))


        table.mime_type.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The identifier of the MIME content type and sub-type describing the resource file"),
                  T("MIME content type and sub-type as described in [RFC 2046]. (As of this document, the current IANA registered MIME types are listed at http://www.iana.org/assignments/media-types/)")))


        table.size.writable = False
        table.size.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The integer indicating the size of the resource file"),
                  T("Approximate size of the resource file in bytes.")))

        # fixme: This should be handled under the hood
        table.uri.writable = False
        table.uri.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The identifier of the hyperlink for the resource file"),
                  T("A full absolute URI, typically a Uniform Resource Locator that can be used to retrieve the resource over the Internet.")))


        #table.deref_uri.writable = False
        #table.deref_uri.readable = False

        table.base64encode.label = T("Encode in message?")
        table.base64encode.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Should this file be encoded into the CAP Message and sent?"),
                  T("Selecting this will encode the file in Base 64 encoding (which converts it into text) and sends it embedded in the CAP message. This is useful in one-way network where the sender cannot create URLs publicly accessible over the internet.")))


        table.digest.writable=False
        table.digest.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The code representing the digital digest ('hash') computed from the resource file"),
                  T("Calculated using the Secure Hash Algorithm (SHA-1).")))





        # ---------------------------------------------------------------------
        tablename = "cap_info_area"
        # FIXME: Use gis_location here and convert wkt to WGS84
        table = self.define_table(tablename,
                                  Field("area_desc", required=True),
                                  Field("polygon", "text"),
                                  Field("circle"),
                                  Field("geocode", "list:string"),
                                  Field("altitude", "integer"),
                                  Field("ceiling", "integer"),
                                  location_id(),
                                  *s3.meta_fields())

        table.area_desc.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The affected area of the alert message"),
                  T("A text description of the affected area.")))


        table.polygon.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Points defining a polygon that delineates the affected area"),
                  T("")))


        table.circle.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A point and radius delineating the affected area"),
                  T("The circular area is represented by a central point given as a coordinate pair followed by a radius value in kilometers.")))


        table.geocode.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The geographic code delineating the affected area"),
                  T("Any geographically-based code to describe a message target area, in the form. The key is a user-assigned string designating the domain of the code, and the content of value is a string (which may represent a number) denoting the value itself (e.g., name='ZIP' and value='54321'). This should be used in concert with an equivalent description in the more universally understood polygon and circle forms whenever possible.")))

        table.altitude.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The specific or minimum altitude of the affected area"),
                  T("If used with the ceiling element this value is the lower limit of a range. Otherwise, this value specifies a specific altitude. The altitude measure is in feet above mean sea level.")))


        table.ceiling.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The maximum altitude of the affected area"),
                  T("must not be used except in combination with the 'altitude' element. The ceiling measure is in feet above mean sea level.")))

        # ---------------------------------------------------------------------
        tablename = "cap_info"

        # CAP info Event Category (category)
        cap_info_category_opts = {
            "Geo":T("Geophysical (inc. landslide)"),
            "Met":T("Meteorological (inc. flood)"),
            "Safety":T("General emergency and public safety"),
            "Security":T("Law enforcement, military, homeland and local/private security"),
            "Rescue":T("Rescue and recovery"),
            "Fire":T("Fire suppression and rescue"),
            "Health":T("Medical and public health"),
            "Env":T("Pollution and other environmental"),
            "Transport":T("Public and private transportation"),
            "Infra":T("Utility, telecommunication, other non-transport infrastructure"),
            "CBRNE":T("Chemical, Biological, Radiological, Nuclear or High-Yield Explosive threat or attack"),
            "Other":T("Other events"),
        }
        # CAP info Response Type (responseType)
        cap_info_responseType_opts = {
            "Shelter":T("Shelter - Take shelter in place or per instruction"),
            "Evacuate":T("Evacuate - Relocate as instructed in the instruction"),
            "Prepare":T("Prepare - Make preparations per the instruction"),
            "Execute":T("Execute - Execute a pre-planned activity identified in instruction"),
            "Avoid":T("Avoid - Avoid the subject event as per the instruction"),
            "Monitor":T("Monitor - Attend to information sources as described in instruction"),
            "Assess":T("Assess - Evaluate the information in this message."),
            "AllClear":T("AllClear - The subject event no longer poses a threat"),
            "None":T("None - No action recommended"),
        }
        # CAP info urgency
        cap_info_urgency_opts = {
            "Immediate":T("Respone action should be taken immediately"),
            "Expected":T("Response action should be taken soon (within next hour)"),
            "Future":T("Responsive action should be taken in the near future"),
            "Past":T("Responsive action is no longer required"),
            "Unknown":T("Unknown"),
        }
        # CAP info severity
        cap_info_severity_opts = {
            "Extreme":T("Extraordinary threat to life or property"),
            "Severe":T("Significant threat to life or property"),
            "Moderate":T("Possible threat to life or property"),
            "Minor":T("Minimal to no known threat to life or property"),
            "Unknown":T("Severity unknown"),
        }
        # CAP info certainty
        cap_info_certainty_opts = {
            "Observed":T("Observed: determined to have occurred or to be ongoing"),
            "Likely":T("Likely (p > ~50%)"),
            "Possible":T("Possible but not likely (p <= ~50%)"),
            "Unlikely":T("Not expected to occur (p ~ 0)"),
            "Unknown":T("Certainty unknown"),
        }
        table = self.define_table(tablename,
                                  Field("language"),
                                  Field("category", "text",
                                        requires=IS_IN_SET(cap_info_category_opts,
                                            multiple=True)), # 0 or more allowed
                                  Field("event", required=True),
                                  Field("response_type",
                                        requires=IS_IN_SET(cap_info_responseType_opts,
                                            multiple=True)), # 0 or more allowed
                                  Field("urgency",
                                        required=True,
                                        notnull=True,
                                        requires=IS_IN_SET(cap_info_urgency_opts)),
                                  Field("severity",
                                        required=True,
                                        notnull=True,
                                        requires=IS_IN_SET(cap_info_severity_opts)),
                                  Field("certainty",
                                        required=True,
                                        notnull=True,
                                        requires=IS_IN_SET(cap_info_certainty_opts)),
                                  Field("audience", "text"),
                                  Field("event_code", "list:string"), # this is actually a map. Handled by the widget
                                  Field("effective", "datetime"),
                                  Field("onset", "datetime"),
                                  Field("expires", "datetime"),
                                  Field("sender_name"),
                                  Field("headline"),
                                  Field("description", "text"),
                                  Field("instruction", "text"),
                                  Field("contact", "text"),
                                  Field("web", requires=IS_NULL_OR(IS_URL())),
                                  Field("parameter", "list:string"),
                                  Field("resource", "list:reference cap_info_resource"),
                                  Field("area", "list:reference cap_info_area"),
                                  *s3.meta_fields())

        table.language.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the language of the information"),
                  T("Code Values: Natural language identifier per [RFC 3066]. If not present, an implicit default value of 'en-US' will be assumed.")))


        table.category.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the category of the subject event of the alert message"),
                  T("You may select multiple categories by holding down control and then selecting the items.")))

        table.event.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text denoting the type of the subject event of the alert message"),
                  T("")))

        table.response_type.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the type of action recommended for the target audience"),
                  T("Multiple response types can be selected by holding down control and then selecting the items")))
        #table.response_type.widget = S3MultiSelectWidget()

        table.urgency.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the urgency of the subject event of the alert message"),
                  T("The urgency, severity, and certainty of the information collectively distinguish less emphatic from more emphatic messages." +
                    "'Immediate' - Responsive action should be taken immediately" +
                    "'Expected' - Responsive action should be taken soon (within next hour)" +
                    "'Future' - Responsive action should be taken in the near future" +
                    "'Past' - Responsive action is no longer required" +
                    "'Unknown' - Urgency not known")))


        table.severity.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the severity of the subject event of the alert message"),
                  T("The urgency, severity, and certainty elements collectively distinguish less emphatic from more emphatic messages." +
                  "'Extreme' - Extraordinary threat to life or property" +
                  "'Severe' - Significant threat to life or property" +
                  "'Moderate' - Possible threat to life or property" +
                  "'Minor' - Minimal to no known threat to life or property" +
                  "'Unknown' - Severity unknown")))


        table.certainty.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the certainty of the subject event of the alert message"),
                  T("The urgency, severity, and certainty elements collectively distinguish less emphatic from more emphatic messages." +
                  "'Observed' - Determined to have occurred or to be ongoing" +
                  "'Likely' - Likely (p > ~50%)" +
                  "'Possible' - Possible but not likely (p <= ~50%)" +
                  "'Unlikely' - Not expected to occur (p ~ 0)" +
                  "'Unknown' - Certainty unknown")))


        table.audience.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The intended audience of the alert message"),
                  T("")))


        table.event_code.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A system-specific code identifying the event type of the alert message"),
                  T("Any system-specific code for events, in the form of key-value pairs. (e.g., SAME, FIPS, ZIP).")))


        table.effective.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The effective time of the information of the alert message"),
                  T("If not specified, the effective time shall be assumed to be the same the time the alert was sent.")))

        table.onset.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The expected time of the beginning of the subject event of the alert message"),
                  T("")))


        table.expires.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The expiry time of the information of the alert message"),
                  T("If this item is not provided, each recipient is free to enforce its own policy as to when the message is no longer in effect.")))


        table.sender_name.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text naming the originator of the alert message"),
                  T("The human-readable name of the agency or authority issuing this alert.")))


        table.headline.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text headline of the alert message"),
                  T("A brief human-readable headline.  Note that some displays (for example, short messaging service devices) may only present this headline; it should be made as direct and actionable as possible while remaining short.  160 characters may be a useful target limit for headline length.")))


        table.description.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The subject event of the alert message"),
                  T("An extended human readable description of the hazard or event that occasioned this message.")))


        table.instruction.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The recommended action to be taken by recipients of the alert message"),
                  T("An extended human readable instruction to targeted recipients.  If different instructions are intended for different recipients, they should be represented by use of multiple information blocks. You can use a different information block also to specify this information in a different language.")))


        table.web.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A URL associating additional information with the alert message"),
                  T("A full, absolute URI for an HTML page or other text resource with additional or reference information regarding this alert.")))


        table.contact.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The contact for follow-up and confirmation of the alert message"),
                  T("")))

        table.resource.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Additional files supplimenting the alert message."),
                  T("")))


        table.parameter.label = T("Parameters")
        table.parameter.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A system-specific additional parameter associated with the alert message"),
                  T("Any system-specific datum, in the form of key-value pairs.")))
        table.parameter.widget = S3KeyValueWidget()

        table.area.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The affected area of the alert"),
                  T("")))

        # ---------------------------------------------------------------------
        tablename = "cap_alert"

        # CAP alert Status Code (status)
        cap_alert_status_code_opts = {
            "Actual":T("Actual - actionable by all targeted recipients"),
            "Exercise":T("Exercise - only for designated participants (decribed in note)"),
            "System":T("System - for internal functions"),
            "Test":T("Test - testing, all recipients disregard"),
            "Draft":T("Draft - not actionable in its current form"),
        }
        # CAP alert message type (msgType)
        cap_alert_msgType_code_opts = {
            "Alert":T("Alert: Initial information requiring attention by targeted recipients"),
            "Update":T("Update: Update and supercede earlier message(s)"),
            "Cancel":T("Cancel: Cancel earlier message(s)"),
            "Ack":T("Ack: Acknowledge receipt and acceptance of the message(s)"),
            "Error":T("Error: Indicate rejection of the message(s)"),
        }

        table = self.define_table(tablename,
                                  # identifier string, as was recieved.
                                  Field("identifier", unique=True),
                                  Field("sender"),
                                  Field("sent", "datetime", writable=False, readable=False), # this is maintained by the system
                                  Field("status",
                                        requires=IS_IN_SET(cap_alert_status_code_opts)),
                                  Field("msg_type",
                                        requires=IS_IN_SET(cap_alert_msgType_code_opts)),
                                  Field("source"),
                                  Field("scope"),
                                  Field("restriction"), # text decribing the restriction for scope=restricted
                                  Field("addresses", "list:string"),
                                  Field("codes", "list:string"),
                                  Field("note"),
                                  Field("info", "list:reference cap_info"),
                                  Field("reference", "list:reference cap_alert"),
                                  Field("incidents"),
                                  *s3.meta_fields())
        table.identifier.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A unique identifier of the alert message"),
                  T("A number or string uniquely identifying this message, assigned by the sender. Must notnclude spaces, commas or restricted characters (< and &).")))

        table.sender.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The identifier of the sender of the alert message"),
                  T("This is guaranteed by assigner to be unique globally; e.g., may be based on an Internet domain name. Must not include spaces, commas or restricted characters (< and &).")))

        table.status.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the appropriate handling of the alert message"),
                  T("")))

        table.msg_type.label = T("Message Type")
        table.msg_type.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The nature of the alert message"),
                  T("A number or string uniquely identifying this message, assigned by the sender. Must notnclude spaces, commas or restricted characters (< and &).")))

        table.source.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text identifying the source of the alert message"),
                  T("The particular source of this alert; e.g., an operator or a specific device.")))

        table.scope.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Denotes the intended distribution of the alert message"),
                  T("Who is this alert for?")))

        table.restriction.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text describing the rule for limiting distribution of the restricted alert message"),
                  T("Used when scope is 'Restricted'.")))

        #todo: provide a better way to add multiple addresses, do not ask the user to delimit it themselves
        #      this should eventually use the CAP contacts
        table.addresses.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The group listing of intended recipients of the alert message"),
                  T("Required when scope is 'Private', optional when scope is 'Public' or 'Restricted'. Each recipient shall be identified by an identifier or an address.")))
        #table.addresses.widget = S3CAPAddressesWidget

        table.codes.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Codes for special handling of the message"),
                  T("Any user-defined flags or special codes used to flag the alert message for special handling.")))
        table.codes.widget = S3KeyValueWidget()

        table.note.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text describing the purpose or significance of the alert message"),
                  T("The message note is primarily intended for use with <status> “Exercise” and <msgType> “Error”")))

        # FIXME: this should not be manually entered, needs a widget
        table.reference.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The group listing identifying earlier message(s) referenced by the alert message"),
                  T("The extended message identifier(s) (in the form sender,identifier,sent) of an earlier CAP message or messages referenced by this one. If multiple messages are referenced, they shall be separated by whitespace.")))
        #table.references.widget = S3CAPAlertReferencesWidget

        table.incidents.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A list of incident(s) referenced by the alert message"),
                  T("Used to collate multiple messages referring to different aspects of the same incident. If multie incident identifiers are referenced, they SHALL be separated by whitespace.  Incident names including whitespace SHALL be surrounded by double-quotes.")))
        #table.addresses.widget = S3CAPIncidentsWidget

        #table.info.widget = S3CAPMultipleInfoWidget
        table.info.widget = lambda k, v: SQLFORM(current.db.cap_info)
        table.info.label = T("Information")

        ADD_ALERT = T("Create CAP Alert")
        LIST_ALERTS = T("List alerts")
        s3.crud_strings[tablename] = Storage(
            title_create = ADD_ALERT,
            title_display = T("CAP Alert"),
            title_list = LIST_ALERTS,
            title_update = T("Update CAP alert"), # this will create a new "Update" alert?
            title_upload = T("Import CAP Alerts"),
            title_search = T("Search CAP Alerts"),
            subtitle_create = T("Create and Broadcast CAP Alert"),
            subtitle_list = T("Listing of CAP Alerts created and received"),
            label_list_button = LIST_ALERTS,
            label_create_button = ADD_ALERT,
            label_delete_button = T("Delete CAP Alert"),
            msg_record_created = T("CAP alert created"),
            msg_record_modified = T("CAP alert modified"),
            msg_record_deleted = T("CAP alert deleted"),
            msg_list_empty = T("No CAP alerts to show"))

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        return Storage()

