odoo.define('clickup_connector.TasksSelectorFormView', function (require) {
    'use strict';

    let FormRenderer = require('web.FormRenderer');
    let FormView = require('web.FormView');
    let viewRegistry = require('web.view_registry');
    let core = require('web.core');
    let qweb = core.qweb;

    let TasksSelectorFormRenderer = FormRenderer.extend({
        events: _.extend({}, FormRenderer.prototype.events, {
            'click .open_tasks_selector': '_openTasksSelectorWizard'
        }),

        _openTasksSelectorWizard: function (e) {
            $.blockUI();

            let self = this;
            let resId = this.state.res_id;
            this._rpc({
                model: 'clicker.space',
                method: 'get_tasks_hierarchy',
                args: [resId]
            }).then(function (data) {
                if ($('div.modal').length)
                    $('div.modal').remove();

                let template = qweb.render('TasksHierarchy', {data: data});
                $('body').append(template);

                $.unblockUI();

                $('.list_row').on('click', function (e) {
                    let listRow = $(e.target);
                    if ($(listRow).hasClass('o_data_cell')) {
                        let listId = $(listRow).attr('list-id');
                        if ($(listRow).attr('folded') === 'true') {
                            $('.task_row[list-id="' + listId + '"]').css('display', 'table-row');
                            $('.fa-caret-right[list-id="' + listId + '"]').toggleClass('fa-caret-right fa-caret-down');
                            $(listRow).attr('folded', "false");
                        } else {
                            $('.task_row[list-id="' + listId + '"]').css('display', 'none');
                            $('.fa-caret-down[list-id="' + listId + '"]').toggleClass('fa-caret-down fa-caret-right');
                            $(listRow).attr('folded', "true");
                        }
                    }
                });

                $('.list_checkbox').on('change', function (e) {
                    let listId = $(e.target).attr('list-id');
                    $('.task_row[list-id="' + listId + '"] input').prop('checked', $(e.target).prop('checked'));
                });

                $('.close_modal').on('click', function () {
                    $('div.modal').css('display', 'none');
                });

                $('.import_tasks').on('click', function () {
                    let tasksIds = $('input[type="checkbox"]')
                        .toArray()
                        .filter(item => $(item).prop('checked') && $(item).hasClass('task_checkbox'))
                        .map(item => $(item).attr('line-id'));
                    self._rpc({
                        model: 'clicker.space',
                        method: 'import_tasks',
                        args: [resId, tasksIds]
                    }).then(_ => {
                        location.reload();
                    });
                });

            });
        },

    });

    let TasksSelectorFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Renderer: TasksSelectorFormRenderer
        }),
    });

    viewRegistry.add('tasks_selector', TasksSelectorFormView);

    return TasksSelectorFormView;

});
