(function ($) {
    $(document).ready(function () {
        // cosmetic fix, move the link from col3 to the forefront
        $(".s3_reference").each(function () {
            var row = $(this).parents("tr").eq(0)
            row.find("td").eq(0).append(row.find(".w2p_fc a.colorbox"));
        });
    });
})(jQuery, undefined);
