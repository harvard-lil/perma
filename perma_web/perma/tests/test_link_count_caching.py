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

def test_link_count_for_orgs(organization, org_user_factory, link_factory):
    """ We do some link count tallying on save. Let's make sure
    we're adjusting the counts on the orgs """

    org_user = org_user_factory(organizations = ([organization]))
    link_count = organization.link_count
    link = link_factory(created_by=org_user, submitted_url="http://example.com", organization=organization)
    link.save()

    organization.refresh_from_db()
    assert link_count + 1 == organization.link_count

    link.safe_delete()
    link.save()

    organization.refresh_from_db()
    assert link_count == organization.link_count


def test_link_count_for_registrars(registrar, link_user_factory, organization_factory, org_link_factory):
    """ We do some link count tallying on save. Let's make sure
    we're adjusting the counts on the registrars """

    registrar_to_which_user_belongs = registrar
    link_count = registrar_to_which_user_belongs.link_count
    org_managed_by_registrar = organization_factory(registrar=registrar_to_which_user_belongs)
    registrar_user = link_user_factory(registrar=registrar_to_which_user_belongs)
    link = org_link_factory(created_by=registrar_user, submitted_url="http://example.com", organization=org_managed_by_registrar)
    link.save()

    registrar_to_which_user_belongs.refresh_from_db()
    assert link_count + 1 == registrar_to_which_user_belongs.link_count

    link.safe_delete()
    link.save()

    registrar_to_which_user_belongs.refresh_from_db()
    assert link_count == registrar_to_which_user_belongs.link_count
