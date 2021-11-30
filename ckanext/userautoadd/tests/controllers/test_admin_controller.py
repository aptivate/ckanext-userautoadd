from ckan.plugins.toolkit import config
import ckan.tests.helpers as helpers
import ckan.tests.factories as factories


class TestCustomAdminController(helpers.FunctionalTestBase):
    def setup(self):
        super(TestCustomAdminController, self).setup()
        self.admin = factories.User(name='adminuser', sysadmin=True)
        self.editor = factories.User(name='editor')
        self.user = factories.User(name='user')
        self.organization = factories.Organization(
            name='mapaction', user=self.admin)
        self.site_url = config.get("ckan.site_url")

        self.app = self._get_test_app()

    def test_editor_user(self):
        context = {'ignore_auth': True}
        helpers.call_action(
            'organization_member_create',
            context,
            id=self.organization['id'],
            username=self.editor['name'],
            role='editor'
        )

        env = {'REMOTE_USER': self.editor['name'].encode('utf-8')}
        response = self.app.get(
            url='%s/ckan-admin/trash' % self.site_url,
            extra_environ=env,
        )
        assert "Purge" in response.body
        assert response.status_int == 200

    def test_admin_user(self):
        env = {'REMOTE_USER': self.admin['name'].encode('utf-8')}
        response = self.app.get(
            url='%s/ckan-admin/trash' % self.site_url,
            extra_environ=env,
        )
        assert "Purge" in response.body
        assert response.status_int == 200

    def test_random_user(self):
        env = {'REMOTE_USER': self.user['name'].encode('utf-8')}
        response = self.app.get(
            url='%s/ckan-admin/trash' % self.site_url,
            extra_environ=env,
            expect_errors=True
        )
        assert response.status_int == 403

    def test_no_user(self):
        """Test without a loged in user"""
        env = {'REMOTE_USER': ''}
        response = self.app.get(
            url='%s/ckan-admin/trash' % self.site_url,
            extra_environ=env,
            expect_errors=True
        )
        assert response.status_int == 403
