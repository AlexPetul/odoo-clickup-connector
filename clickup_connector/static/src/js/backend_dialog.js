odoo.define('clickup_connector.ClickerBackendDialog', function (require) {
    'use strict';

    var core = require('web.core');
    var Dialog = require('web.Dialog');

    var _t = core._t;

    var CropImageDialog = Dialog.include({

        start: function () {
            $('footer').css('display', 'none');
            return this._super.apply(this, arguments);
        },
    });
    return CropImageDialog;
});