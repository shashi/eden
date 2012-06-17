(function ($) {
    function kv_pairs() {
        var self = $(this),
            ref = self.find("li").eq(0).clone(),
            plus=$('<a href="javascript:void(0)">+</a>').click(function() {new_item();}),
            delim = '`';

        function new_item () {
            self.find("li").each(function() {
              var trimmed = $.trim($(this).find(":hidden").val());
              if (trimmed=='' || trimmed == delim) $(this).remove();
            });

            ref.find("a").remove();
            var clone = ref.clone();
            clone.find(":text").val("")

            self.append(clone)
            return false;
        }

        self.find(".value,.key").live('keypress', function (e) {
            return (e.which == 13) ? $(this).is(".value") && new_item() : true;
        }).live('blur', function () {
            var li = $(this).parents().eq(0)
            li.find(":hidden").val(li.find(".key").val() + delim + li.find(".value").val())
        })

        self.find(".value:last").after(plus);
    }

    $.fn.dbReference = function (form_url) {
        var id = $(this).attr('id'),
            forms_wrap = $('#' + id + '_nested_forms'),
            more_button = $('#' + id + '_new_item');

        more_button.click(function () {
            console.log(form_url);
            $.ajax({
                url: form_url,
                type: 'GET',
                data: {standalone_form: 1},
                success: function (data) {
                    var new_form = $('<li class="nested_form"></li>').html(data);
                    new_form.find('.key_value_widget').each(kv_pairs);
                    forms_wrap.append(new_form);
                }
            });
        });
    }


    $(document).ready(function () {
        $('.nested_form [type=submit]').live('click', function () {
            var form_container = $(this).parents('.nested_form').eq(0);
            controls = form_container.find('input,textbox,select')
            data = {}
            controls.each(function () {
                var name = $(this).attr('name');
                var value = $(this).attr('value');

                if ($(this).is('input')) {
                    data[name] = value;
                }
            });
            console.log(data);
            alert('Form data has been logged');
            return false;
        });
        $('.key_value_widget').each(kv_pairs);
    });
})(jQuery, undefined);
