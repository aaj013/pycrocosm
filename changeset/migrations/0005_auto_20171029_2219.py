# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-29 22:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0004_changeset_bbox_set'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='changeset',
            name='user',
        ),
        migrations.DeleteModel(
            name='Changeset',
        ),
    ]