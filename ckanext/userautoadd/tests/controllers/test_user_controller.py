from ckan.plugins.toolkit import config
import ckan.tests.helpers as helpers
import ckan.tests.factories as factories


class TestOverrideUserController(helpers.FunctionalTestBase):
    def setup(self):
        super(TestOverrideUserController, self).setup()
        self.user = factories.User(name='somename', email='user@mapaction.org')
        self.normal_user = factories.User()
        self.site_url = config.get("ckan.site_url")

        self.app = self._get_test_app()

    def test_override_controller(self):
        env = {'REMOTE_USER': self.user['name'].encode('utf-8')}
        response = self.app.get(
            url='%s/user/edit/%s' % (self.site_url, self.user['id']),
            extra_environ=env,
        )
        assert response.status_int == 200
        assert "Change password" not in response.body

    def test_normal_user(self):
        env = {'REMOTE_USER': self.normal_user['name'].encode('utf-8')}
        response = self.app.get(
            url='%s/user/edit/%s' % (self.site_url, self.normal_user['id']),
            extra_environ=env,
        )
        assert response.status_int == 200
        assert "Change password" in response.body
