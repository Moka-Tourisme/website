odoo.define('website_geonames', function () {
    $(document).ready(function () {
        $('.zip_id').select2({
            placeholder: "Search a city",
            minimumInputLength: 3,
            maximumSelectionSize: 1,
            ajax: {
                url: "/city/get_zip",
                dataType: "json",
                delay: 250,
                data: function (term) {
                    return {
                        query: term,
                        limit: 25,
                    }
                },
                processResults: function (data) {
                    let ret = [];
                    _.each(data, function (x) {
                        ret.push({
                            id: x.id,
                            text: x.display_name,
                            zip: x.name,
                            city: x.city_id[1],
                            country: x.country_id[0],
                            state: x.state_id[0],
                        });
                    });
                    return {
                        results: ret,
                    };
                },
                cache: true,
            },
        });
    });

    $(".zip_id").change(function () {
        let data = $(".zip_id").select2('data');
        $('select[name="country_id"]').val(data.country).trigger('change');
        setTimeout(function () {
            $('select[name="state_id"]').val(data.state);
        }, 1000)
        $('input[name="city"]').val(data.city);
        $('input[name="zip"]').val(data.zip);
    })
});