# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-05 23:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('changeset', '0002_changeset_is_open'),
    ]

    operations = [
        migrations.AlterField(
            model_name='changeset',
            name='close_datetime',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
