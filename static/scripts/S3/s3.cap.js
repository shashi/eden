(function($, JSON) {
    // Logic for forms
    function init_cap_form($form) {
        // On change in scope
        $form.find('[name=scope]').change(function() {
            var scope = $(this).val(),
                $restriction = $form.find('[name=restriction]'),
                $recipients  = $form.find('[name=addresses]'),

                disable = function (item) {
                            item.parents('tr').eq(0).hide().prev().hide();
                          } //XXX: hide or disable?
                enable  = function (item) {
                            item.parents('tr').eq(0).show().prev().show();
                          };

            switch(scope) {
                case 'Public':
                    disable($restriction);
                    disable($recipients);
                    break;
                case 'Restricted':
                    enable($restriction);
                    disable($recipients);
                    break;
                case 'Private':
                    disable($restriction);
                    enable($recipients);
                    break;
            }
        });
    }

    function is_cap_template() {
        return $('.cap_template_form').length > 0;
    }

    function is_cap_info_template() {
        return $('.cap_info_template_form').length > 0;
    }

    function init_template_form($form) {

        /* templates-specific stuff */
        function get_settings() {
            try {
                var settings = $.parseJSON($form.find('[name=template_settings]').val());
                return settings || {};
            } catch (e) {
                console.log("Error occured parsing: ", $form.find('[name=template_settings]').val());
                return {};
            }
        }

        function set_settings(settings) {
            console.log(settings);
            $form.find('[name=template_settings]').val(JSON.stringify(settings));
        }

        // set as template!
        $form.find("[name=is_template]").attr("checked", "checked");

        function inheritable_flag(field, $e) {
            var name = 'can_edit-' + field,
                $label = $('<label for="' + name + '">' +
                                (S3.i18n.cap_editable || 'Editable') + '</label>'),
                $checkbox = $('<input type="checkbox" name="' + name +'"/>');

            $checkbox.click(function () {
                var settings = get_settings();
                settings.editable = settings.editable || {};
                settings.editable[field] = $(this).is(':checked');
                set_settings(settings);
            });

            var settings = get_settings();
            if (settings.editable && settings.editable[field]) {
                $checkbox.attr('checked', 'checked');
            }

            $e.append($label);
            $e.append($checkbox);
        }

        if (is_cap_template()) {
            inheritable_fields = 'sender,sent,status,msg_type,source,scope,' +
                                 'restriction,addresses,codes,note,reference,' +
                                 'incidents'.split(',');
            tablename = 'cap_alert';

        } else {
            inheritable_fields = 'category,event,response_type,urgency,' +
                                 'severity,certainty,audience,event_code,' +
                                 'effective,onset,expires,sender_name,headline,' +
                                 'description,instruction,contact,web,parameter'.split(',');
            tablename = 'cap_info';
        }

        $form.find("tr").each(function () {
            var $tr = $(this),
                id = $tr.attr("id");

            if (id.match("__row$")) {
                // this row contains the field and comment
                var name = id.replace(tablename + "_", "").replace("__row", ""),
                    $comment = $tr.find("td.w2p_fc") || $tr.find("td").eq(1);
                if (inheritable_fields.indexOf(name) >= 0) {
                    inheritable_flag(name, $comment);
                }
            }
        });
    }

    $(document).ready(function() {
        $('form').each(function() {
            var _formname = $(this).find('[name=_formname]').val(),
                alert_form = 'cap_alert',
                alert_info = 'cap_info';

            if (_formname.substring(0, alert_form.length) == alert_form) {
                init_cap_form($(this));
                if (is_cap_template()) {
                    init_template_form($(this));
                }
            } else if (_formname.substring(0, alert_info.length) == alert_info) {
                //init_info_form($(this));
                if (is_cap_info_template()) {
                    init_template_form($(this));
                }
            }
        });
    });
})(jQuery, JSON, undefined);
