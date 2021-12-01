from ckan.controllers.admin import AdminController
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.model as model
import ckan.logic as logic
from ckan.lib.base import BaseController
from ckan.plugins.toolkit import c, request, _
from ckan.authz import has_user_permission_for_group_or_org


class CustomAdminController(BaseController):
    def __before__(self, action, **params):
        super(CustomAdminController, self).__before__(action, **params)
        context = {'model': model,
                   'user': c.user, 'auth_user_obj': c.userobj}
        if action == u"trash" and c.user:
            # 'delete_dataset' is a permision that only
            #  org `editor` or `admin` has
            if has_user_permission_for_group_or_org('mapaction',
                                                    c.user,
                                                    'delete_dataset'):
                context['ignore_auth'] = True
            try:
                logic.check_access('sysadmin', context, {})
            except logic.NotAuthorized:
                base.abort(403, _(
                    'Need to be system administrator to administer'))
        else:
            x = AdminController()
            x.__before__(action, **params)

    def trash(self):
        c.deleted_revisions = model.Session.query(
            model.Revision).filter_by(state=model.State.DELETED)
        c.deleted_packages = model.Session.query(
            model.Package).filter_by(state=model.State.DELETED)
        if not request.params or (len(request.params) == 1 and '__no_cache__'
                                  in request.params):
            return base.render('admin/trash.html')
        else:
            # NB: we repeat retrieval of revisions
            # this is obviously inefficient (but probably not *that* bad)
            # but has to be done to avoid (odd) sqlalchemy errors (when doing
            # purge packages) of form: "this object already exists in the
            # session"
            msgs = []
            if ('purge-packages' in request.params) or ('purge-revisions' in
                                                        request.params):
                if 'purge-packages' in request.params:
                    revs_to_purge = []
                    for pkg in c.deleted_packages:
                        revisions = [x[0] for x in pkg.all_related_revisions]
                        # ensure no accidental purging of other(non-deleted)
                        # packages initially just avoided purging revisions
                        # where non-deleted packages were affected
                        # however this lead to confusing outcomes e.g.
                        # we succesfully deleted revision in which package
                        # was deleted (so package now active again) but no
                        # other revisions
                        problem = False
                        for r in revisions:
                            affected_pkgs = set(r.packages).\
                                difference(set(c.deleted_packages))
                            if affected_pkgs:
                                msg = _('Cannot purge package %s as '
                                        'associated revision %s includes '
                                        'non-deleted packages %s')
                                msg = msg % (pkg.id, r.id, [pkg.id for r
                                                            in affected_pkgs])
                                msgs.append(msg)
                                problem = True
                                break
                        if not problem:
                            revs_to_purge += [r.id for r in revisions]
                    model.Session.remove()
                else:
                    revs_to_purge = [rev.id for rev in c.deleted_revisions]
                revs_to_purge = list(set(revs_to_purge))
                for id in revs_to_purge:
                    revision = model.Session.query(model.Revision).get(id)
                    try:
                        # TODO deleting the head revision corrupts the edit
                        # page Ensure that whatever 'head' pointer is used
                        # gets moved down to the next revision
                        model.repo.purge_revision(revision, leave_record=False)
                    except Exception, inst:
                        msg = _('Problem purging revision %s: %s') % (id, inst)
                        msgs.append(msg)
                h.flash_success(_('Purge complete'))
            else:
                msgs.append(_('Action not implemented.'))

            for msg in msgs:
                h.flash_error(msg)
            h.redirect_to(controller='admin', action='trash')
