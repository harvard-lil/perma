from tasks.once import reconcile_user_link_counts
from invoke import Context


def test_reconcile_user_link_counts_sets_cache_from_non_deleted_links(link_user, link_factory):
    """ Task should set LinkUser.link_count to the count of non-deleted links created by each user """
    live = link_factory(created_by=link_user, submitted_url="http://example.com/live")
    deleted = link_factory(created_by=link_user, submitted_url="http://example.com/deleted")
    deleted.safe_delete()
    deleted.save()

    link_user.link_count = 99
    link_user.save(update_fields=['link_count'])

    ctx = Context()
    updated = reconcile_user_link_counts(ctx)

    link_user.refresh_from_db()
    assert updated >= 1
    assert link_user.link_count == 1
    assert live.user_deleted is False


def test_reconcile_user_link_counts_dry_run_does_not_write(link_user, link_factory):
    link_factory(created_by=link_user, submitted_url="http://example.com")
    link_user.link_count = 99
    link_user.save(update_fields=['link_count'])

    ctx = Context()
    count = reconcile_user_link_counts(ctx, dry_run=True)

    link_user.refresh_from_db()
    assert count >= 1
    assert link_user.link_count == 99


def test_link_count_do_not_increment_after_saving_a_deleted_link(org_user, link_factory):
    """ Re-saving a user-deleted link must not count it as a new link """
    organization = org_user.organizations.first()
    registrar = organization.registrar
    link = link_factory(
        created_by=org_user,
        submitted_url="http://example.com",
        organization=organization,
    )
    org_user.refresh_from_db()
    organization.refresh_from_db()
    registrar.refresh_from_db()
    assert org_user.link_count == 1
    assert organization.link_count == 1
    assert registrar.link_count == 1
    link.safe_delete() 
    link.save()

    org_user.refresh_from_db()
    organization.refresh_from_db()
    registrar.refresh_from_db()
    assert org_user.link_count == 0
    assert organization.link_count == 0
    assert registrar.link_count == 0

    link.save()
    org_user.refresh_from_db()
    organization.refresh_from_db()
    registrar.refresh_from_db()
    assert org_user.link_count == 0
    assert organization.link_count == 0
    assert registrar.link_count == 0


def test_link_count_regular_user(link_user, link_factory):
    """ We do some link count tallying on save """
    link_count = link_user.link_count
    link = link_factory(created_by=link_user, submitted_url="http://example.com")
    link_user.refresh_from_db()
    assert link_count + 1 == link_user.link_count

    link.safe_delete()
    link.save()

    link_user.refresh_from_db()
    assert link_count == link_user.link_count

def test_link_count_for_orgs(org_user, link_factory):
    """ We do some link count tallying on save. Let's make sure
    we're adjusting the counts on the orgs """
    organization = org_user.organizations.first()
    link_count = organization.link_count
    link = link_factory(created_by=org_user, submitted_url="http://example.com", organization=organization)
    link.save()

    organization.refresh_from_db()
    assert link_count + 1 == organization.link_count

    link.safe_delete()
    link.save()

    organization.refresh_from_db()
    assert link_count == organization.link_count


def test_link_count_for_registrars(registrar_user, link_factory):
    """ We do some link count tallying on save. Let's make sure
    we're adjusting the counts on the registrars """

    org_managed_by_registrar = registrar_user.registrar.organizations.first()
    link_count = registrar_user.registrar.link_count
    link = link_factory(created_by=registrar_user, submitted_url="http://example.com", organization=org_managed_by_registrar)
    link.save()

    registrar_user.registrar.refresh_from_db()
    assert link_count + 1 == registrar_user.registrar.link_count

    link.safe_delete()
    link.save()

    registrar_user.registrar.refresh_from_db()
    assert link_count == registrar_user.registrar.link_count
