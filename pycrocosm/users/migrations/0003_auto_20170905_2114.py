# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-05 21:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20170905_2111'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UserProfile',
            new_name='UserData',
        ),
    ]
