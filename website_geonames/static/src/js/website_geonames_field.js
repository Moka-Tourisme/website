odoo.define('website_sale_geonames.WebsiteSale', function (require) {
    'use strict';

    const {WebsiteSale} = require('website_sale.website_sale');

    WebsiteSale.include({
        events: {
            'change form .js_product:first input[name="add_qty"]': '_onChangeAddQuantity',
            'mouseup .js_publish': '_onMouseupPublish',
            'touchend .js_publish': '_onMouseupPublish',
            'change .oe_cart input.js_quantity[data-product-id]': '_onChangeCartQuantity',
            'click .oe_cart a.js_add_suggested_products': '_onClickSuggestedProduct',
            'click a.js_add_cart_json': '_onClickAddCartJSON',
            'click .a-submit': '_onClickSubmit',
            'change form.js_attributes input, form.js_attributes select': '_onChangeAttribute',
            'mouseup form.js_add_cart_json label': '_onMouseupAddCartLabel',
            'touchend form.js_add_cart_json label': '_onMouseupAddCartLabel',
            'click .show_coupon': '_onClickShowCoupon',
            'submit .o_wsale_products_searchbar_form': '_onSubmitSaleSearch',
            'change select[name="country_id"]': '_onChangeCountry',
            'change #shipping_use_same': '_onChangeShippingUseSame',
            'click .toggle_summary': '_onToggleSummary',
            'click #add_to_cart, .o_we_buy_now, #products_grid .o_wsale_product_btn .a-submit': 'async _onClickAdd',
            'click input.js_product_change': 'onChangeVariant',
            'change .js_main_product [data-attribute_exclusions]': 'onChangeVariant',
            'change oe_advanced_configurator_modal [data-attribute_exclusions]': 'onChangeVariant',
            'click .o_product_page_reviews_link': '_onClickReviewsLink',
            'change select.zip_id': '_onZipIDChange',
        },

        /**
         * @override
         */
        start: function () {
            this._super.apply(this, arguments);
            this.$zip_id = this.$el.find(".zip_id");
            this.$country_id = this.$el.find("[name=country_id]");
            this.$state_id = this.$el.find("[name=state_id]");
            this.$city = this.$el.find("[name=city]");
            this.$zip = this.$el.find("[name=zip]");
            this.choices = new Choices(document.getElementsByClassName("zip_id")[0], {
                allowHTML: true,
                searchEnabled: true,
                searchResultLimit: 25
            })
            this.choices.input.element.addEventListener('keyup', this._updateCountries.bind(this))
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        _updateCountries: async function () {
            const query = this.choices.input.element.value;
            const data = await this._rpc({
                route: '/city/get_zip',
                params: {
                    'query': query,
                }
            })
            const countries = data.map((rec) => {
                return {
                    value: rec.id,
                    label: rec.display_name,
                    customProperties: {
                        zip: rec.name,
                        state: rec.state_id[0],
                        country: rec.country_id[0],
                        city: rec.city_id[1]
                    }
                }
            });
            this.choices.setChoices(countries, 'value', 'label', true);
        },

        /**
         * @private
         * @override
         */
        _changeCountry: async function () {
            const self = this;
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
                        if (self.data.state) {
                            self.$state_id.val(self.data.state).trigger('change');
                        }
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
            return true;
        },


        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         */
        _onZipIDChange: async function () {
            this.data = this.choices.getValue().customProperties;
            this.$country_id.val(this.data.country).trigger('change');
            this.$city.val(this.data.city).trigger('change');
            this.$zip.val(this.data.zip).trigger('change');
        },
    })
});