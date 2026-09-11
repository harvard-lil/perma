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


def test_moving_folder_into_org_updates_org_and_registrar_counts(org_user, folder_factory, link_factory):
    """ Moving a folder into an org must update org and registrar counts, not the user's """
    organization = org_user.organizations.first()
    registrar = organization.registrar
    subfolder = folder_factory(parent=org_user.root_folder, name="to-move")
    link_factory(created_by=org_user, submitted_url="http://example.com/a").move_to_folder_for_user(subfolder, org_user)
    link_factory(created_by=org_user, submitted_url="http://example.com/b").move_to_folder_for_user(subfolder, org_user)

    org_user.refresh_from_db()
    organization.refresh_from_db()
    registrar.refresh_from_db()
    user_count = org_user.link_count
    org_count = organization.link_count
    registrar_count = registrar.link_count

    subfolder.parent = organization.shared_folder
    subfolder.save()

    org_user.refresh_from_db()
    organization.refresh_from_db()
    registrar.refresh_from_db()
    assert org_user.link_count == user_count
    assert organization.link_count == org_count + 2
    assert registrar.link_count == registrar_count + 2


def test_moving_folder_out_of_org_updates_org_and_registrar_counts(org_user, folder_factory, link_factory):
    """ Moving a folder out of an org must decrement org and registrar counts, not the user's """
    organization = org_user.organizations.first()
    registrar = organization.registrar
    subfolder = folder_factory(parent=organization.shared_folder, name="to-move")
    link_factory(created_by=org_user, submitted_url="http://example.com").move_to_folder_for_user(subfolder, org_user)

    org_user.refresh_from_db()
    organization.refresh_from_db()
    registrar.refresh_from_db()
    user_count = org_user.link_count
    org_count = organization.link_count
    registrar_count = registrar.link_count

    subfolder.parent = org_user.root_folder
    subfolder.save()

    org_user.refresh_from_db()
    organization.refresh_from_db()
    registrar.refresh_from_db()
    assert org_user.link_count == user_count
    assert organization.link_count == org_count - 1
    assert registrar.link_count == registrar_count - 1


def test_moving_folder_between_orgs_same_registrar_does_not_change_registrar_count(org_user, organization_factory, folder_factory, link_factory):
    """ Same-registrar org folder movements must change org counts and leave the registrar unchanged """
    source = org_user.organizations.first()
    dest = organization_factory(registrar=source.registrar)
    subfolder = folder_factory(parent=source.shared_folder, name="to-move")
    link_factory(created_by=org_user, submitted_url="http://example.com").move_to_folder_for_user(subfolder, org_user)

    source.refresh_from_db()
    dest.refresh_from_db()
    source.registrar.refresh_from_db()
    source_count = source.link_count
    dest_count = dest.link_count
    registrar_count = source.registrar.link_count

    subfolder.parent = dest.shared_folder
    subfolder.save()

    source.refresh_from_db()
    dest.refresh_from_db()
    source.registrar.refresh_from_db()
    assert source.link_count == source_count - 1
    assert dest.link_count == dest_count + 1
    assert source.registrar.link_count == registrar_count


def test_moving_folder_between_orgs_different_registrar_transfers_registrar_count(org_user, organization_factory, folder_factory, link_factory):
    """ Moving a folder to an org on another registrar must update both org and registrar counts """
    source = org_user.organizations.first()
    dest = organization_factory()
    subfolder = folder_factory(parent=source.shared_folder, name="to-move")
    link_factory(created_by=org_user, submitted_url="http://example.com").move_to_folder_for_user(subfolder, org_user)

    source.refresh_from_db()
    dest.refresh_from_db()
    source.registrar.refresh_from_db()
    dest.registrar.refresh_from_db()
    source_count = source.link_count
    dest_count = dest.link_count
    source_registrar_count = source.registrar.link_count
    dest_registrar_count = dest.registrar.link_count

    subfolder.parent = dest.shared_folder
    subfolder.save()

    source.refresh_from_db()
    dest.refresh_from_db()
    source.registrar.refresh_from_db()
    dest.registrar.refresh_from_db()
    assert source.link_count == source_count - 1
    assert dest.link_count == dest_count + 1
    assert source.registrar.link_count == source_registrar_count - 1
    assert dest.registrar.link_count == dest_registrar_count + 1

