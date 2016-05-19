import nose.tools

import ckan.tests.helpers as helpers
import ckan.tests.factories as factories


class TestUserCreate(helpers.FunctionalTestBase):
    def setup(self):
        super(TestUserCreate, self).setup()
        self.admin = factories.User(name='admin')
        self.organization = factories.Organization(
            name='mapaction', user=self.admin)

    @classmethod
    def _apply_config_changes(cls, cfg):
        plugins = set(cfg['ckan.plugins'].strip().split())
        plugins.add('userautoadd')
        cfg['ckan.plugins'] = ' '.join(plugins)

    @helpers.change_config('ckan.userautoadd.organization_name',
                           'mapaction')
    @helpers.change_config('ckan.userautoadd.organization_role',
                           'editor')
    def test_new_user_added_to_organization(self):
        user = helpers.call_action(
            'user_create',
            email='test@example.com',
            name='testuser',
            password='abc123')

        organization = helpers.call_action(
            'organization_show',
            context={'user': self.admin['name']},
            id=self.organization['id'])

        org_users = {o['name']: o for o in organization['users']}

        nose.tools.assert_true(user['name'] in org_users)

        org_user = org_users[user['name']]

        nose.tools.assert_equal(org_user['capacity'], 'editor')
