# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UpdateQueue'
        db.create_table(u'mirroring_updatequeue', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action', self.gf('django.db.models.fields.CharField')(default='update', max_length=10)),
            ('json', self.gf('django.db.models.fields.TextField')()),
            ('sent', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'mirroring', ['UpdateQueue'])


    def backwards(self, orm):
        # Deleting model 'UpdateQueue'
        db.delete_table(u'mirroring_updatequeue')


    models = {
        u'mirroring.updatequeue': {
            'Meta': {'ordering': "['pk']", 'object_name': 'UpdateQueue'},
            'action': ('django.db.models.fields.CharField', [], {'default': "'update'", 'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json': ('django.db.models.fields.TextField', [], {}),
            'sent': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['mirroring']