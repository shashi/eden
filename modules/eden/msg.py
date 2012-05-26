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

__all__ = ["S3MessagingModel",
           "S3CAPModel",
           "S3InboundEmailModel",
           "S3SMSModel",
           "S3SubscriptionModel",
           "S3TropoModel",
           "S3TwitterModel",
           "S3XFormsModel",
        ]

from gluon import *
from gluon.storage import Storage
from ..s3 import *

# =============================================================================
class S3MessagingModel(S3Model):
    """
        Messaging Framework
        - core models defined here
    """

    names = ["msg_log",
             "msg_limit",
             #"msg_tag",
             "msg_outbox",
             #"msg_channel",
             "msg_message_id",
            ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3
        msg = current.msg

        UNKNOWN_OPT = current.messages.UNKNOWN_OPT

        # Message priority
        msg_priority_opts = {
            3:T("High"),
            2:T("Medium"),
            1:T("Low")
        }
        # ---------------------------------------------------------------------
        # Message Log - all Inbound & Outbound Messages
        # ---------------------------------------------------------------------
        tablename = "msg_log"
        table = self.define_table(tablename,
                                  self.super_link("pe_id", "pr_pentity"),
                                  Field("sender"),        # The name to go out incase of the email, if set used
                                  Field("fromaddress"),   # From address if set changes sender to this
                                  Field("recipient"),
                                  Field("subject", length=78),
                                  Field("message", "text"),
                                  #Field("attachment", "upload", autodelete = True), #TODO
                                  Field("verified", "boolean", default = False),
                                  Field("verified_comments", "text"),
                                  Field("actionable", "boolean", default = True),
                                  Field("actioned", "boolean", default = False),
                                  Field("actioned_comments", "text"),
                                  Field("priority", "integer", default = 1,
                                        requires = IS_NULL_OR(IS_IN_SET(msg_priority_opts)),
                                        label = T("Priority")),
                                  Field("inbound", "boolean", default = False,
                                        represent = lambda direction: \
                                            (direction and ["In"] or ["Out"])[0],
                                        label = T("Direction")),
                                  Field("is_parsed", "boolean", default = False,
                                        represent = lambda status: \
                                            (status and ["Parsed"] or ["Not Parsed"])[0],
                                        label = T("Parsing Status")),
                                  Field("reply", "text" ,
                                        label = T("Reply")),                                        
                                  *s3.meta_fields())

        self.configure(tablename,
                       list_fields=["id",
                                    "inbound",
                                    "pe_id",
                                    "fromaddress",
                                    "recipient",
                                    "subject",
                                    "message",
                                    "verified",
                                    #"verified_comments",
                                    "actionable",
                                    "actioned",
                                    #"actioned_comments",
                                    #"priority",
                                    "is_parsed",
                                    "reply"
                                    ])

        # Components
        self.add_component("msg_outbox", msg_log="message_id")

        # Reusable Message ID
        message_id = S3ReusableField("message_id", db.msg_log,
                                     requires = IS_NULL_OR(IS_ONE_OF(db, "msg_log.id")),
                                     # FIXME: Subject works for Email but not SMS
                                     represent = self.message_represent,
                                     ondelete = "RESTRICT")

        # ---------------------------------------------------------------------
        # Message Limit
        #  Used to limit the number of emails sent from the system
        #  - works by simply recording an entry for the timestamp to be checked against
        # @ToDo: have separate limits for Email & SMS
        tablename = "msg_limit"
        table = self.define_table(tablename,
                                  *s3.timestamp())

        # ---------------------------------------------------------------------
        # Message Tag - Used to tag a message to a resource
        # tablename = "msg_tag"
        # table = self.define_table(tablename,
                                  # message_id(),
                                  # Field("resource"),
                                  # Field("record_uuid", # null in this field implies subscription to the entire resource
                                        # type=s3uuid,
                                        # length=128),
                                  # *s3.meta_fields())

        # self.configure(tablename,
                       # list_fields=[ "id",
                                     # "message_id",
                                     # "record_uuid",
                                     # "resource",
                                    # ])

        # ---------------------------------------------------------------------
        # Outbound Messages
        # ---------------------------------------------------------------------
        # Show only the supported messaging methods
        msg_contact_method_opts = msg.MSG_CONTACT_OPTS

        # Valid message outbox statuses
        msg_status_type_opts = {
            1:T("Unsent"),
            2:T("Sent"),
            3:T("Draft"),
            4:T("Invalid")
            }

        opt_msg_status = S3ReusableField("status", "integer",
                                         notnull=True,
                                         requires = IS_IN_SET(msg_status_type_opts,
                                                              zero=None),
                                         default = 1,
                                         label = T("Status"),
                                         represent = lambda opt: \
                                            msg_status_type_opts.get(opt, UNKNOWN_OPT))

        # Outbox - needs to be separate to Log since a single message sent needs different outbox entries for each recipient
        tablename = "msg_outbox"
        table = self.define_table(tablename,
                                  message_id(),
                                  self.super_link("pe_id", "pr_pentity"), # Person/Group to send the message out to
                                  Field("address"),   # If set used instead of picking up from pe_id
                                  Field("pr_message_method",
                                        length=32,
                                        requires = IS_IN_SET(msg_contact_method_opts,
                                                             zero=None),
                                        default = "EMAIL",
                                        label = T("Contact Method"),
                                        represent = lambda opt: \
                                            msg_contact_method_opts.get(opt, UNKNOWN_OPT)),
                                  opt_msg_status(),
                                  Field("system_generated", "boolean", default = False),
                                  Field("log"),
                                  *s3.meta_fields())

        self.configure(tablename,
                       list_fields=[ "id",
                                     "message_id",
                                     "pe_id",
                                     "status",
                                     "log",
                                    ])

        # ---------------------------------------------------------------------
        # Inbound Messages
        # ---------------------------------------------------------------------
        # Channel - For inbound messages this tells which channel the message came in from.
        tablename = "msg_channel"
        table = self.define_table(tablename,
                                  message_id(),
                                  Field("pr_message_method",
                                        length=32,
                                        requires = IS_IN_SET(msg_contact_method_opts,
                                                             zero=None),
                                        default = "EMAIL"),
                                  Field("log"),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        return Storage(
                msg_message_id=message_id,
            )

    # -------------------------------------------------------------------------
    @staticmethod
    def message_represent(id):
        """ Represent a Message in the Log """

        NONE = current.messages.NONE
        if not id:
            return NONE

        db = current.db
        s3db = current.s3db
        table = s3db.msg_log
        query = (table.id == id)

        record = db(query).select(table.subject,
                                  limitby=(0, 1)).first()
        if not record:
            return NONE

        if record.subject:
            # EMail will use Subject
            return record.subject
        # SMS/Tweet will use 1st 80 characters from body
        text = record.message
        if len(text) < 80:
            return text
        else:
            return "%s..." % text[:76]

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

        table.resource.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Additional files supplimenting the alert message."),
                  T("")))


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


        table.deref_uri.writable = False
        table.deref_uri.readable = False

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


        table.area.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The affected area of the alert"),
                  T("")))




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
                                  Field("location", location_id()),
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
            "Shelter":T("Take shelter in place or per <instruction>"),
            "Evacuate":T("Relocate as instructed in the <instruction>"),
            "Prepare":T("Make preparations per the <instruction>"),
            "Execute":T("Execute a pre-planned activity identified in <instruction>"),
            "Avoid":T("Avoid the subject event as per the <instruction>"),
            "Monitor":T("Attend to information sources as described in <instruction>"),
            "Assess":T("Evaluate the information in this message.  (This value SHOULD NOT be used in public warning applications.)"),
            "AllClear":T("The subject event no longer poses a threat or concern and any follow on action is described in <instruction>"),
            "None":T("No action recommended"),
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
                                  Field("category",
                                        requires=IS_IN_SET(cap_info_category_opts),
                                        multiple=True), # 0 or more allowed
                                  Field("event", required=True),
                                  Field("response_type",
                                        requires=IS_IN_SET(cap_info_responseType_opts),
                                        multiple=True),
                                  Field("urgency",
                                        required=True,
                                        notnull=True,
                                        requires=IS_IN_SET(cap_info_urgency_opts)),
                                  Field("severity",
                                        required=True,
                                        notnull=True,
                                        requires=IS_IN_SET(cap_info_severity_opts)),
                                  Field("severity",
                                        required=True,
                                        notnull=True,
                                        requires=IS_IN_SET(cap_info_certainty_opts)),
                                  Field("audience"),
                                  Field("event_code", "list:string"), # this is actually a map. Handled by the widget
                                  Field("effective", "datetime"),
                                  Field("onset", "datetime"),
                                  Field("expires", "datetime"),
                                  Field("sender_name"),
                                  Field("headline"),
                                  Field("description"),
                                  Field("instruction"),
                                  Field("web", requires=IS_NULL_OR(IS_URL())),
                                  Field("contact"),
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


        table.parameter.label = T(_("Parameters"))
        table.parameter.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("A system-specific additional parameter associated with the alert message"),
                  T("Any system-specific datum, in the form of key-value pairs.")))


        # ---------------------------------------------------------------------
        tablename = "cap_alert"

        # CAP alert Status Code (status)
        cap_alert_status_code_opts = {
            "Actual":T("Actionable by all targeted recipients"),
            "Exercise":T("Actionable only by designated exercise participants; exercise identifier SHOULD appear in <note>"),
            "System":T("For messages that support alert network internal functions"),
            "Test":T("Technical testing only, all recipients disregard"),
            "Draft":T("preliminary template or draft, not actionable in its current form"),
        }
        # CAP alert message type (msgType)
        cap_alert_msgType_code_opts = {
            "Alert":T("Initial information requiring attention by targeted recipients"),
            "Update":T("Update and supercede earlier message(s)"),
            "Cancel":T("Cancel earlier message(s)"),
            "Ack":T("Acknowledge receipt and acceptance of the message(s)"),
            "Error":T("Indicate rejection of the message(s)"),
        }

        table = self.define_table(tablename,
                                  # identifier string, as was recieved.
                                  Field("identifier", unique=True),
                                  Field("sender"),
                                  Field("sent", "datetime", writable=False), # this is maintained by the system
                                  Field("status",
                                        requires=IS_IN_SET(cap_alert_status_code_opts,
                                                             zero=None)),
                                  Field("msg_type",
                                        requires=IS_IN_SET(cap_alert_status_code_opts)),
                                  Field("source"),
                                  Field("scope"),
                                  Field("restriction"), # text decribing the restriction for scope=restricted
                                  Field("addresses"),
                                  Field("codes"),
                                  Field("note"),
                                  Field("incidents"),
                                  Field("info", "list:reference cap_info"),
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
                  T("Required when scope is 'Private', optional when scope is 'Public' or 'Restricted'. Each recipient shall be identified by an identifier or an address. Multiple space-delimited addresses may be included.  Addresses including whitespace must be enclosed in double-quotes.")))
        #table.addresses.widget = S3CAPAddressesWidget

        table.codes.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("Codes for special handling of the message"),
                  T("Any user-defined flags or special codes used to flag the alert message for special handling.")))
        #table.codes.widget = S3CAPKeyValueWidget

        table.note.comment = DIV(
              _class="tooltip",
              _title="%s|%s" % (
                  T("The text describing the purpose or significance of the alert message"),
                  T("The message note is primarily intended for use with <status> “Exercise” and <msgType> “Error”")))

        # FIXME: this should not be manually entered, needs a widget
        table.references.comment = DIV(
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

        # ---------------------------------------------------------------------
        # Pass variables back to global scope (response.s3.*)
        return Storage()

# =============================================================================
class S3InboundEmailModel(S3Model):
    """
        Inbound Email

        Outbound Email is handled via deployment_settings
    """

    names = ["msg_inbound_email_settings",
             "msg_inbound_email_status",
             "msg_email_inbox",
            ]

    def model(self):

        # @ToDo: i18n labels
        T = current.T
        s3 = current.response.s3

        # ---------------------------------------------------------------------
        tablename = "msg_inbound_email_settings"
        table = self.define_table(tablename,
                                  Field("server"),
                                  Field("protocol",
                                        requires = IS_IN_SET(["imap", "pop3"],
                                                             zero=None)),
                                  Field("use_ssl", "boolean"),
                                  Field("port", "integer"),
                                  Field("username"),
                                  Field("password"),
                                  # Set true to delete messages from the remote
                                  # inbox after fetching them.
                                  Field("delete_from_server", "boolean"),
                                  *s3.meta_fields())

        # Incoming Email
        tablename = "msg_email_inbox"
        table = self.define_table(tablename,
                                  Field('sender', notnull=True),
                                  Field('subject', length=78),    # RFC 2822
                                  Field('body', 'text'),
                                  *s3.meta_fields())
        table.sender.requires = IS_EMAIL()
        table.sender.label = T('Sender')
        #table.sender.comment = SPAN("*", _class="req")
        table.subject.label = T('Subject')
        table.body.label = T('Body')
        VIEW_EMAIL_INBOX = T('View Email InBox')
        s3.crud_strings[tablename] = Storage(
            #title_create = T('Add Incoming Email'),
            title_display = T('Email Details'),
            title_list = VIEW_EMAIL_INBOX,
            #title_update = T('Edit Email'),
            title_search = T('Search Email InBox'),
            subtitle_list = T('Email InBox'),
            label_list_button = VIEW_EMAIL_INBOX,
            #label_create_button = T('Add Incoming Email'),
            #msg_record_created = T('Email added'),
            #msg_record_modified = T('Email updated'),
            msg_record_deleted = T('Email deleted'),
            msg_list_empty = T('No Emails currently in InBox'))

        # Status
        tablename = "msg_inbound_email_status"
        table = self.define_table(tablename,
                                  Field("status"))

        # ---------------------------------------------------------------------
        return Storage()

# =============================================================================
class S3SMSModel(S3Model):
    """
        SMS: Short Message Service

        These can be sent through a number of different gateways
        - modem
        - api
        - smtp
        - tropo
    """

    names = ["msg_setting",
             "msg_modem_settings",
             "msg_api_settings",
             "msg_smtp_to_sms_settings",
            ]

    def model(self):

        T = current.T
        s3 = current.response.s3
        msg = current.msg

        # ---------------------------------------------------------------------
        # Settings
        tablename = "msg_setting"
        table = self.define_table(tablename,
                                  Field("outgoing_sms_handler",
                                        length=32,
                                        requires = IS_IN_SET(msg.GATEWAY_OPTS,
                                                             zero=None)),
                                  # Moved to deployment_settings
                                  #Field("default_country_code", "integer",
                                  #      default=44),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        tablename = "msg_modem_settings"
        table = self.define_table(tablename,
                                  # Nametag to remember account - To be used later
                                  #Field("account_name"),
                                  Field("modem_port"),
                                  Field("modem_baud", "integer", default = 115200),
                                  Field("enabled", "boolean", default = True),
                                  # To be used later
                                  #Field("preference", "integer", default = 5),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        tablename = "msg_api_settings"
        table = self.define_table(tablename,
                                  Field("url",
                                        default = "https://api.clickatell.com/http/sendmsg"),
                                  Field("parameters",
                                        default="user=yourusername&password=yourpassword&api_id=yourapiid"),
                                  Field("message_variable", "string",
                                        default = "text"),
                                  Field("to_variable", "string",
                                        default = "to"),
                                  Field("enabled", "boolean", default = True),
                                  # To be used later
                                  #Field("preference", "integer", default = 5),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        tablename = "msg_smtp_to_sms_settings"
        table = self.define_table(tablename,
                                  # Nametag to remember account - To be used later
                                  #Field("account_name"),
                                  Field("address", length=64,
                                        requires=IS_NOT_EMPTY()),
                                  Field("subject", length=64),
                                  Field("enabled", "boolean", default = True),
                                  # To be used later
                                  #Field("preference", "integer", default = 5),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        return Storage()

# =============================================================================
class S3SubscriptionModel(S3Model):
    """
        Handle Subscription
        - currently this is just for Saved Searches
    """

    names = ["msg_subscription"]

    def model(self):

        T = current.T
        db = current.db
        auth = current.auth
        s3 = current.response.s3

        person_id = self.pr_person_id

        # @ToDo: Use msg.CONTACT_OPTS
        msg_subscription_mode_opts = {
                                        1:T("Email"),
                                        #2:T("SMS"),
                                        #3:T("Email and SMS")
                                    }
        # @ToDo: Move this to being a component of the Saved Search
        #        (so that each search can have it's own subscription options)
        # @ToDo: Make Conditional
        # @ToDo: CRUD Strings
        tablename = "msg_subscription"
        table = self.define_table(tablename,
                                  Field("user_id","integer",
                                        default = auth.user_id,
                                        requires = IS_NOT_IN_DB(db, "msg_subscription.user_id"),
                                        readable = False,
                                        writable = False
                                        ),
                                  Field("subscribe_mode","integer",
                                        default = 1,
                                        represent = lambda opt: \
                                            msg_subscription_mode_opts.get(opt, None),
                                        readable = False,
                                        requires = IS_IN_SET(msg_subscription_mode_opts,
                                                             zero=None)
                                        ),
                                  Field("subscription_frequency",
                                        requires = IS_IN_SET(["daily",
                                                              "weekly",
                                                              "monthly"]),
                                        default = "daily",
                                        ),
                                  person_id(label = T("Person"),
                                            default = auth.s3_logged_in_person()),
                                  *s3.meta_fields())

        self.configure("msg_subscription",
                       list_fields=["subscribe_mode",
                                    "subscription_frequency"])

        # ---------------------------------------------------------------------
        return Storage()

# =============================================================================
class S3TropoModel(S3Model):
    """
        Tropo can be used to send & receive SMS, Twitter & XMPP

        https://www.tropo.com
    """

    names = ["msg_tropo_settings",
             "msg_tropo_scratch",
            ]

    def model(self):

        #T = current.T
        s3 = current.response.s3

        # ---------------------------------------------------------------------
        tablename = "msg_tropo_settings"
        table = self.define_table(tablename,
                                  Field("token_messaging"),
                                  #Field("token_voice"),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        # Tropo Scratch pad for outbound messaging
        tablename = "msg_tropo_scratch"
        table = self.define_table(tablename,
                                  Field("row_id","integer"),
                                  Field("message_id","integer"),
                                  Field("recipient"),
                                  Field("message"),
                                  Field("network")
                                )

        # ---------------------------------------------------------------------
        return Storage()

# =============================================================================
class S3TwitterModel(S3Model):

    names = ["msg_twitter_settings",
             "msg_twitter_search",
             "msg_twitter_search_results"
            ]

    def model(self):

        T = current.T
        db = current.db
        s3 = current.response.s3

        # ---------------------------------------------------------------------
        tablename = "msg_twitter_settings"
        table = self.define_table(tablename,
                                  Field("pin"),
                                  Field("oauth_key",
                                        readable = False, writable = False),
                                  Field("oauth_secret",
                                        readable = False, writable = False),
                                  Field("twitter_account", writable = False),
                                  *s3.meta_fields())

        self.configure(tablename,
                       onvalidation=self.twitter_settings_onvalidation)

        # ---------------------------------------------------------------------
        # Twitter Search Queries
        tablename = "msg_twitter_search"
        table = self.define_table(tablename,
                                  Field("search_query", length = 140),
                                  *s3.meta_fields())

        # ---------------------------------------------------------------------
        tablename = "msg_twitter_search_results"
        table = self.define_table(tablename,
                                  Field("tweet", length=140),
                                  Field("posted_by"),
                                  Field("posted_at"),
                                  Field("twitter_search", db.msg_twitter_search),
                                  *s3.meta_fields())

        #table.twitter_search.requires = IS_ONE_OF(db, "twitter_search.search_query")
        #table.twitter_search.represent = lambda id: db(db.msg_twitter_search.id == id).select(db.msg_twitter_search.search_query,
                                                                                              #limitby = (0, 1)).first().search_query

        #self.add_component(table, msg_twitter_search="twitter_search")

        self.configure(tablename,
                       list_fields=[ "id",
                                     "tweet",
                                     "posted_by",
                                     "posted_at",
                                     "twitter_search",
                                    ])

        # ---------------------------------------------------------------------
        return Storage()

    # -------------------------------------------------------------------------
    @staticmethod
    def twitter_settings_onvalidation(form):
        """
            Complete oauth: take tokens from session + pin from form, and do the 2nd API call to Twitter
        """

        T = current.T
        session = current.session
        settings = current.deployment_settings
        s3 = session.s3
        vars = form.vars

        if vars.pin and s3.twitter_request_key and s3.twitter_request_secret:
            try:
                import tweepy
            except:
                raise HTTP(501, body=T("Can't import tweepy"))

            oauth = tweepy.OAuthHandler(settings.twitter.oauth_consumer_key,
                                        settings.twitter.oauth_consumer_secret)
            oauth.set_request_token(s3.twitter_request_key,
                                    s3.twitter_request_secret)
            try:
                oauth.get_access_token(vars.pin)
                vars.oauth_key = oauth.access_token.key
                vars.oauth_secret = oauth.access_token.secret
                twitter = tweepy.API(oauth)
                vars.twitter_account = twitter.me().screen_name
                vars.pin = "" # we won't need it anymore
                return
            except tweepy.TweepError:
                session.error = T("Settings were reset because authenticating with Twitter failed")
        # Either user asked to reset, or error - clear everything
        for k in ["oauth_key", "oauth_secret", "twitter_account"]:
            vars[k] = None
        for k in ["twitter_request_key", "twitter_request_secret"]:
            s3[k] = ""

# =============================================================================
class S3XFormsModel(S3Model):
    """
        XForms are used by the ODK Collect mobile client

        http://eden.sahanafoundation.org/wiki/BluePrint/Mobile#Android
    """

    names = ["msg_xforms_store"]

    def model(self):

        #T = current.T
        s3 = current.response.s3

        # ---------------------------------------------------------------------
        # SMS store for persistence and scratch pad for combining incoming xform chunks
        tablename = "msg_xforms_store"
        table = self.define_table(tablename,
                                  Field("sender", "string", length = 20),
                                  Field("fileno", "integer"),
                                  Field("totalno", "integer"),
                                  Field("partno", "integer"),
                                  Field("message", "string", length = 160)
                                )

        # ---------------------------------------------------------------------
        return Storage()

# END =========================================================================
