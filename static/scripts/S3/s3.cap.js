(function($, JSON) {

    function get_table($form) {
        var _formname = $form.find('[name=_formname]').val(),
            alert_table = 'cap_alert',
            info_table = 'cap_info';

        if (_formname.substring(0, alert_table.length) == alert_table) {
            return alert_table;
        }

        if (_formname.substring(0, info_table.length) == info_table) {
            return info_table;
        }

        return '';
    }

    function is_cap_template() {
        return $('.cap_template_form').length > 0;
    }

    function is_cap_info_template() {
        return $('.cap_info_template_form').length > 0;
    }

    function get_template_fields(table) {
        if (table=='cap_alert') {
            return ('sender,sent,status,msg_type,source,scope,' +
                    'restriction,addresses,codes,note,reference,' +
                    'incidents').split(',');

        } else if (table=='cap_info') {
             return ('category,event,response_type,urgency,' +
                     'severity,certainty,audience,event_code,' +
                     'effective,onset,expires,sender_name,headline,' +
                     'description,instruction,contact,web,parameter').split(',');
        }
        return [];
    }
    window.fields = get_template_fields;


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

        function load_template_data(data) {
            var tablename = get_table($form),
                fields = get_template_fields(tablename),
                values, settings = {};
            if (tablename == 'cap_alert') {
                values = data['$_cap_alert'][0];
                settings = $.parseJSON(values.template_settings) || {};
            } else if (tablename == 'cap_info') {
                // FIXME: Multiple info :/
                values = data['$_cap_alert'][0]['$_cap_info'][0];
                settings = $.parseJSON(values.template_settings) || {};
            }

            $.each(fields, function (i, f) {
                try {
                    var $f = $form.find('[name=' + f +']')
                    //console.log('[name=' + f +']', $f, values);
                    if ($f.is(":text") || $f.is("textarea") || $f.is("select")) {
                        console.log(f, values[f]);
                        switch(typeof(values[f])) {
                        case 'string':
                        case 'undefined':
                            $f.val(values[f] || '');
                            if (settings.editable && settings.editable[f]) {
                                $f.attr('disabled', 'disabled')
                                  .attr('title', '');
                            } else {
                                $f.removeAttr('disabled')
                                  // TODO: i18n
                                  .attr('title', 'This field is locked by the template');
                            }
                            break;
                        case 'object':
                            break;
                        }
                    }
                } catch(e) {
                    console.log("ERROR", e);
                }
            });
        }

        function apply_template(id) {
            var re = new RegExp('.*\\' + S3.Ap + '\\/'),
                _url = new String(self.location),
                module = _url.replace(re, '').split('?')[0].split('/')[0],
                url = [S3.Ap, module, "template", id].join("/") + ".s3json";
            console.log(url);
            $.ajax({
                url: url,
                type: 'GET',
                dataType: 'json',
                success: function(data) {
                    load_template_data(data);
                },
                error: function(e) {
                    console.log(e);
                    // FIXME: i18n
                    alert("There was an unexpected error loading template data");
                }
            });
        }

        $form.find('[name=template_id]').change(function () {
            apply_template($(this).val());
        });

        window.apply_temp = apply_template;
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

        tablename = get_table($form);
        fields = get_template_fields(tablename);

        $form.find("tr").each(function () {
            var $tr = $(this),
                id = $tr.attr("id");

            if (id.match("__row$")) {
                // this row contains the field and comment
                var name = id.replace(tablename + "_", "").replace("__row", ""),
                    $comment = $tr.find("td.w2p_fc") || $tr.find("td").eq(1);
                if (fields.indexOf(name) >= 0) {
                    inheritable_flag(name, $comment);
                }
            }
        });
    }

    $(document).ready(function() {
        $('form').each(function() {
            if (get_table($(this)) != '') {
                init_cap_form($(this));
                if (is_cap_template() || is_cap_info_template()) {
                    init_template_form($(this));
                }
            }
        });
    });
})(jQuery, JSON, undefined);
