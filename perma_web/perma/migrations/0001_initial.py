# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Registrar'
        db.create_table(u'perma_registrar', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=254)),
            ('website', self.gf('django.db.models.fields.URLField')(max_length=500)),
        ))
        db.send_create_signal(u'perma', ['Registrar'])

        # Adding model 'LinkUser'
        db.create_table(u'perma_linkuser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('email', self.gf('django.db.models.fields.EmailField')(unique=True, max_length=255, db_index=True)),
            ('registrar', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['perma.Registrar'], null=True)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_admin', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('date_joined', self.gf('django.db.models.fields.DateField')(auto_now_add=True, blank=True)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
            ('authorized_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='authorized_by_manager', null=True, to=orm['perma.LinkUser'])),
            ('confirmation_code', self.gf('django.db.models.fields.CharField')(max_length=45, blank=True)),
        ))
        db.send_create_signal(u'perma', ['LinkUser'])

        # Adding M2M table for field groups on 'LinkUser'
        db.create_table(u'perma_linkuser_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('linkuser', models.ForeignKey(orm[u'perma.linkuser'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(u'perma_linkuser_groups', ['linkuser_id', 'group_id'])

        # Adding model 'Link'
        db.create_table(u'perma_link', (
            ('guid', self.gf('django.db.models.fields.CharField')(max_length=255, primary_key=True)),
            ('view_count', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('submitted_url', self.gf('django.db.models.fields.URLField')(max_length=2100)),
            ('creation_timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('submitted_title', self.gf('django.db.models.fields.CharField')(max_length=2100)),
            ('created_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='created_by', null=True, to=orm['perma.LinkUser'])),
            ('vested', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('vested_by_editor', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='vested_by_editor', null=True, to=orm['perma.LinkUser'])),
            ('vested_timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'perma', ['Link'])

        # Adding model 'Asset'
        db.create_table(u'perma_asset', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('link', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['perma.Link'])),
            ('base_storage_path', self.gf('django.db.models.fields.CharField')(max_length=2100, null=True, blank=True)),
            ('favicon', self.gf('django.db.models.fields.CharField')(max_length=2100, null=True, blank=True)),
            ('image_capture', self.gf('django.db.models.fields.CharField')(max_length=2100, null=True, blank=True)),
            ('warc_capture', self.gf('django.db.models.fields.CharField')(max_length=2100, null=True, blank=True)),
            ('pdf_capture', self.gf('django.db.models.fields.CharField')(max_length=2100, null=True, blank=True)),
            ('text_capture', self.gf('django.db.models.fields.CharField')(max_length=2100, null=True, blank=True)),
            ('instapaper_timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('instapaper_hash', self.gf('django.db.models.fields.CharField')(max_length=2100, null=True)),
            ('instapaper_id', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal(u'perma', ['Asset'])


    def backwards(self, orm):
        # Deleting model 'Registrar'
        db.delete_table(u'perma_registrar')

        # Deleting model 'LinkUser'
        db.delete_table(u'perma_linkuser')

        # Removing M2M table for field groups on 'LinkUser'
        db.delete_table('perma_linkuser_groups')

        # Deleting model 'Link'
        db.delete_table(u'perma_link')

        # Deleting model 'Asset'
        db.delete_table(u'perma_asset')


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
            'link': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['perma.Link']"}),
            'pdf_capture': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'}),
            'text_capture': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'}),
            'warc_capture': ('django.db.models.fields.CharField', [], {'max_length': '2100', 'null': 'True', 'blank': 'True'})
        },
        u'perma.link': {
            'Meta': {'object_name': 'Link'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'created_by'", 'null': 'True', 'to': u"orm['perma.LinkUser']"}),
            'creation_timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '255', 'primary_key': 'True'}),
            'submitted_title': ('django.db.models.fields.CharField', [], {'max_length': '2100'}),
            'submitted_url': ('django.db.models.fields.URLField', [], {'max_length': '2100'}),
            'vested': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'vested_by_editor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'vested_by_editor'", 'null': 'True', 'to': u"orm['perma.LinkUser']"}),
            'vested_timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
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
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '45', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'registrar': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['perma.Registrar']", 'null': 'True'})
        },
        u'perma.registrar': {
            'Meta': {'object_name': 'Registrar'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '500'})
        }
    }

    complete_apps = ['perma']