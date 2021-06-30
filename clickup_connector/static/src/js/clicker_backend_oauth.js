odoo.define('clickup_connector.ClickerBackendAuthFormView', function (require) {
    "use strict";

    let FormRenderer = require('web.FormRenderer');
    let FormView = require('web.FormView');
    let viewRegistry = require('web.view_registry');

    let ClickerBackendAuthFormRenderer = FormRenderer.extend({
        events: _.extend({}, FormRenderer.prototype.events, {
            'click .open_oauth_uri': '_openOauthUri',
        }),

        _openOauthUri: function (e) {
            let clientID = $("textarea[name='client_id']").val();
            window.location.href = `https://app.clickup.com/api?client_id=${clientID}&redirect_uri=https://localhost:8069/web`;
        }
    });

    let ClickerBackendAuthFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Renderer: ClickerBackendAuthFormRenderer
        }),
    });

    viewRegistry.add("clicker_backend_form", ClickerBackendAuthFormView);

    return ClickerBackendAuthFormView;

});
