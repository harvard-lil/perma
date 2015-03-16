# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CDXLine'
        db.create_table(u'perma_cdxline', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('urlkey', self.gf('django.db.models.fields.URLField')(max_length=2100)),
            ('raw', self.gf('django.db.models.fields.TextField')()),
            ('asset', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cdx_lines', to=orm['perma.Asset'])),
        ))
        db.send_create_signal(u'perma', ['CDXLine'])


        # Changing field 'Link.creation_timestamp'
        db.alter_column(u'perma_link', 'creation_timestamp', self.gf('django.db.models.fields.DateTimeField')())

    def backwards(self, orm):
        # Deleting model 'CDXLine'
        db.delete_table(u'perma_cdxline')


        # Changing field 'Link.creation_timestamp'
        db.alter_column(u'perma_link', 'creation_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True))

    models = {
        u'perma.asset': {
            'Meta': {'object_name': 'Asset'},
            'base_storage_path': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'}),
            'favicon': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_capture': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'}),
            'instapaper_hash': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True'}),
            'instapaper_id': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'instapaper_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'integrity_check_succeeded': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'last_integrity_check': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'link': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'assets'", 'to': u"orm['perma.Link']"}),
            'pdf_capture': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'}),
            'text_capture': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'}),
            'warc_capture': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'})
        },
        u'perma.cdxline': {
            'Meta': {'object_name': 'CDXLine'},
            'asset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cdx_lines'", 'to': u"orm['perma.Asset']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'raw': ('django.db.models.fields.TextField', [], {}),
            'urlkey': ('django.db.models.fields.URLField', [], {'max_length': '2100'})
        },
        u'perma.folder': {
            'Meta': {'object_name': 'Folder'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'folders_created'", 'null': 'True', 'to': u"orm['perma.LinkUser']"}),
            'creation_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_root_folder': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_shared_folder': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'owned_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'folders'", 'null': 'True', 'to': u"orm['perma.LinkUser']"}),
            'parent': ('mptt.fields.TreeForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': u"orm['perma.Folder']"}),
            u'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            u'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'vesting_org': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'folders'", 'null': 'True', 'to': u"orm['perma.VestingOrg']"})
        },
        u'perma.link': {
            'Meta': {'object_name': 'Link'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'created_links'", 'null': 'True', 'to': u"orm['perma.LinkUser']"}),
            'creation_timestamp': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'dark_archived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'dark_archived_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'darchived_links'", 'null': 'True', 'to': u"orm['perma.LinkUser']"}),
            'dark_archived_robots_txt_blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'folders': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'links'", 'null': 'True', 'symmetrical': 'False', 'to': u"orm['perma.Folder']"}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'submitted_title': ('django.db.models.fields.CharField', [], {'max_length': '2100'}),
            'submitted_url': ('django.db.models.fields.URLField', [], {'max_length': '2100'}),
            'user_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user_deleted_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'vested': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'vested_by_editor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'vested_links'", 'null': 'True', 'to': u"orm['perma.LinkUser']"}),
            'vested_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'vesting_org': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['perma.VestingOrg']", 'null': 'True', 'blank': 'True'}),
            'view_count': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        u'perma.linkuser': {
            'Meta': {'object_name': 'LinkUser'},
            'confirmation_code': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_confirmed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'registrar': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'users'", 'null': 'True', 'to': u"orm['perma.Registrar']"}),
            'root_folder': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['perma.Folder']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'vesting_org': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'users'", 'null': 'True', 'to': u"orm['perma.VestingOrg']"})
        },
        u'perma.registrar': {
            'Meta': {'object_name': 'Registrar'},
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
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
            'date_created': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'registrar': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'vesting_orgs'", 'null': 'True', 'to': u"orm['perma.Registrar']"}),
            'shared_folder': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['perma.Folder']", 'unique': 'True', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['perma']