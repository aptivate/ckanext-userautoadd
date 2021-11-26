import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import ckanext.userautoadd.logic.action.create


class UserautoaddPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IRoutes, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'userautoadd')

    # IActions
    def get_actions(self):
        return {
            'user_create':
            ckanext.userautoadd.logic.action.create.user_create,
        }

    def before_map(self, map):
        controller='ckanext.userautoadd.controllers.admin_controller:CustomAdminController'
        map.connect(
            '/ckan-admin/trash',
            controller=controller,
            action='trash'
            )
        return map