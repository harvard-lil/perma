# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Registrar.default_vesting_org'
        db.add_column(u'perma_registrar', 'default_vesting_org',
                      self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='default_for_registrars', unique=True, null=True, to=orm['perma.VestingOrg']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Registrar.default_vesting_org'
        db.delete_column(u'perma_registrar', 'default_vesting_org_id')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'perma.asset': {
            'Meta': {'object_name': 'Asset'},
            'base_storage_path': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'}),
            'favicon': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_capture': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'}),
            'instapaper_hash': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True'}),
            'instapaper_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'instapaper_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'link': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assets'", 'to': u"orm['perma.Link']"}),
            'pdf_capture': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'}),
            'text_capture': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'}),
            'warc_capture': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'})
        },
        u'perma.folder': {
            'Meta': {'object_name': 'Folder'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'folders_created'", 'null': 'True', 'to': u"orm['perma.LinkUser']"}),
            'creation_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            u'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['perma.Folder']"}),
            u'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            u'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        u'perma.link': {
            'Meta': {'object_name': 'Link'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'created_by'", 'null': 'True', 'to': u"orm['perma.LinkUser']"}),
            'creation_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'dark_archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'dark_archived_robots_txt_blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'folders': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'links'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['perma.Folder']"}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'submitted_title': ('django.db.models.fields.CharField', [], {'max_length': '2100'}),
            'submitted_url': ('django.db.models.fields.URLField', [], {'max_length': '2100'}),
            'user_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user_deleted_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'vested': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'vested_by_editor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'vested_by_editor'", 'null': 'True', 'to': u"orm['perma.LinkUser']"}),
            'vested_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'vesting_org': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['perma.VestingOrg']", 'null': 'True'}),
            'view_count': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        u'perma.linkuser': {
            'Meta': {'object_name': 'LinkUser'},
            'authorized_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'authorized_by_manager'", 'null': 'True', 'to': u"orm['perma.LinkUser']"}),
            'confirmation_code': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'null': 'True', 'symmetrical': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_admin': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'registrar': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['perma.Registrar']", 'null': 'True'}),
            'vesting_org': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['perma.VestingOrg']", 'null': 'True'})
        },
        u'perma.registrar': {
            'Meta': {'object_name': 'Registrar'},
            'default_vesting_org': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'default_for_registrars'", 'unique': 'True', 'null': 'True', 'to': u"orm['perma.VestingOrg']"}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '500'})
        },
        u'perma.stat': {
            'Meta': {'object_name': 'Stat'},
            'creation_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'darchive_robots_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'darchive_takedown_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'disk_usage': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'global_uniques': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'registrar_count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'registrar_member_count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'registry_member_count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'regular_user_count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'unvested_count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'vested_count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'vesting_manager_count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'vesting_member_count': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'vesting_org_count': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        u'perma.vestingorg': {
            'Meta': {'object_name': 'VestingOrg'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'registrar': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['perma.Registrar']", 'null': 'True'})
        }
    }

    complete_apps = ['perma']