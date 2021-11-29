import logging

from ckan.common import config
from paste.deploy.converters import asbool

import ckan.lib.base as base
import ckan.model as model
import ckan.authz as authz
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dictization_functions
from ckan.common import _, c, request
from ckan.controllers.user import UserController


log = logging.getLogger(__name__)

abort = base.abort
render = base.render

check_access = logic.check_access
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized


class OverrideUserController(UserController):
    def edit(self, id=None, data=None, errors=None, error_summary=None):
        context = {'save': 'save' in request.params,
                   'schema': self._edit_form_to_db_schema(),
                   'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj
                   }
        if id is None:
            if c.userobj:
                id = c.userobj.id
            else:
                abort(400, _('No user specified'))
        data_dict = {'id': id}

        try:
            check_access('user_update', context, data_dict)
        except NotAuthorized:
            abort(403, _('Unauthorized to edit a user.'))

        if context['save'] and not data and request.method == 'POST':
            return self._save_edit(id, context)

        try:
            old_data = get_action('user_show')(context, data_dict)

            schema = self._db_to_edit_form_schema()
            if schema:
                old_data, errors = \
                    dictization_functions.validate(old_data, schema, context)

            c.display_name = old_data.get('display_name')
            c.user_name = old_data.get('name')

            data = data or old_data

        except NotAuthorized:
            abort(403, _('Unauthorized to edit user %s') % '')
        except NotFound:
            abort(404, _('User not found'))

        user_obj = context.get('user_obj')

        if not (authz.is_sysadmin(c.user)
                or c.user == user_obj.name):
            abort(403, _('User %s not authorized to edit %s') %
                  (str(c.user), id))

        errors = errors or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}

        try:
            if c.userobj.email.endswith("mapaction.org"):
                vars['org_check'] = True
        except AttributeError:
            # just in case there is a user without email
            pass

        self._setup_template_variables({'model': model,
                                        'session': model.Session,
                                        'user': c.user},
                                       data_dict)

        c.is_myself = True
        c.show_email_notifications = asbool(
            config.get('ckan.activity_streams_email_notifications'))
        c.form = render(self.edit_user_form, extra_vars=vars)

        return render('user/edit.html')
