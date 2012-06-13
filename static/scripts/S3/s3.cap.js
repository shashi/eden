(function ($) {
    $(document).ready(function () {
        $(".nested_form [type=submit]").live('click', function () {
            var form_container = $(this).parents(".nested_form").eq(0);
            controls = form_container.find("input,textbox,select")
            data = {}
            controls.each(function () {
                var name = $(this).attr("name");
                var value = $(this).attr("value");

                if ($(this).is("input")) {
                    data[name] = value;
                }
            });
            console.log(data);
            alert("Form data has been logged");
            return false;
        });
    });
})(jQuery, undefined);
