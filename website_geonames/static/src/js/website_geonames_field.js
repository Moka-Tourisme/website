odoo.define('website_geonames', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');
    const website_sale = require('website_sale.website_sale')
    const rpc = require('web.rpc');

    publicWidget.registry.geonamesAutocomplete = publicWidget.Widget.extend({
        selector: 'form.checkout_autoformat',
        events: {
            'change select.zip_id': '_onZipIDChange',
        },

        /**
         * @override
         */
        start: function () {
            const self = this;
            self.$zip_id = self.$el.find(".zip_id");
            self.$country_id = self.$el.find("[name=country_id]");
            self.$state_id = self.$el.find("[name=state_id]");
            self.$city = self.$el.find("[name=city]");
            self.$zip = self.$el.find("[name=zip]");
            self.choices = new Choices(document.getElementsByClassName("zip_id")[0], {
                allowHTML: true,
                searchEnabled: true,
                searchResultLimit: 25
            })
            self.choices.input.element.addEventListener('keyup', this._updateCountries.bind(this))
            // this._initChoicesGeonames();
        },

        _updateCountries: function () {
            const self = this;
            const query = self.choices.input.element.value;
            rpc.query({
                model: 'res.city.zip',
                method: 'search_read',
                kwargs: {
                    fields: ['id', 'display_name', 'name', 'city_id', 'country_id', 'state_id'],
                    domain: [
                        ['display_name', 'ilike', query]
                    ],
                    limit: 25
                }
            }).then(function (data) {
                    let countries = [];
                    _.each(data, function (country) {
                        countries.push({
                            value: country.id,
                            label: country.display_name,
                            customProperties: {
                                zip: country.name,
                                state: country.state_id[0],
                                country: country.country_id[0],
                                city: country.city_id[1],
                            }
                        })
                    });
                    self.choices.setChoices(
                        countries,
                        'value',
                        'label',
                        true
                    );
                }
            );
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @private
         * @override
         */
        _changeCountry: function () {
            alert("oui");
            if (!$("#country_id").val()) {
                return;
            }
            this._rpc({
                route: "/shop/country_infos/" + $("#country_id").val(),
                params: {
                    mode: $("#country_id").attr('mode'),
                },
            }).then(function (data) {
                // placeholder phone_code
                $("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+' + data.phone_code : '');

                // populate states and display
                var selectStates = $("select[name='state_id']");
                // dont reload state at first loading (done in qweb)
                if (selectStates.data('init') === 0 || selectStates.find('option').length === 1) {
                    if (data.states.length || data.state_required) {
                        selectStates.html('');
                        _.each(data.states, function (x) {
                            var opt = $('<option>').text(x[1])
                                .attr('value', x[0])
                                .attr('data-code', x[2]);
                            selectStates.append(opt);
                        });
                        selectStates.parent('div').show();
                    } else {
                        selectStates.val('').parent('div').hide();
                    }
                    selectStates.data('init', 0);
                } else {
                    selectStates.data('init', 0);
                }

                // manage fields order / visibility
                if (data.fields) {
                    if ($.inArray('zip', data.fields) > $.inArray('city', data.fields)) {
                        $(".div_zip").before($(".div_city"));
                    } else {
                        $(".div_zip").after($(".div_city"));
                    }
                    var all_fields = ["street", "zip", "city", "country_name"]; // "state_code"];
                    _.each(all_fields, function (field) {
                        $(".checkout_autoformat .div_" + field.split('_')[0]).toggle($.inArray(field, data.fields) >= 0);
                    });
                }

                if ($("label[for='zip']").length) {
                    $("label[for='zip']").toggleClass('label-optional', !data.zip_required);
                    $("label[for='zip']").get(0).toggleAttribute('required', !!data.zip_required);
                }
                if ($("label[for='zip']").length) {
                    $("label[for='state_id']").toggleClass('label-optional', !data.state_required);
                    $("label[for='state_id']").get(0).toggleAttribute('required', !!data.state_required);
                }
            });
        },

        /**
         * @private
         */
        _adaptCountrySelect: async function () {
            const self = this;
            self.$country_id.val(self.data.country).trigger('change');
            return true;
        },


        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         */
        _onZipIDChange: async function () {
            const self = this;
            self.data = self.choices.getValue().customProperties;
            await this._adaptCountrySelect();
            setTimeout(function () {
                (self.$state_id.val(self.data.state).trigger('change'));
            },1000)
            self.$city.val(self.data.city).trigger('change');
            self.$zip.val(self.data.zip).trigger('change');
        },
    })

});