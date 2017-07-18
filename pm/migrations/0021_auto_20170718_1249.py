# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-07-18 19:49
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pm', '0020_auto_20170117_1341'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='team',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='project',
            name='tm_cap',
            field=models.IntegerField(blank=True, default=0, verbose_name='Time and Materials flag'),
        ),
    ]