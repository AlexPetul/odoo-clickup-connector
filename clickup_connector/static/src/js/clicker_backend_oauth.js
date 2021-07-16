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
            let clientID = this.state.data.client_id;
            let clientSecret = this.state.data.client_secret;
            let modelId = this.state.context.active_id;
            window.location.href = `https://app.clickup.com/api?client_id=${clientID}&redirect_uri=${window.location.protocol}//${window.location.host}/oauth/${modelId}/${clientID}/${clientSecret}/`;
        },
    });

    let ClickerBackendAuthFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Renderer: ClickerBackendAuthFormRenderer
        }),
    });

    viewRegistry.add("clicker_backend_form", ClickerBackendAuthFormView);

    return ClickerBackendAuthFormView;

});
