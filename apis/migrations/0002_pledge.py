# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-06 21:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Pledge',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('contents', models.TextField(null=True)),
                ('category', models.IntegerField(default=0)),
                ('candidate', models.CharField(max_length=10)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'pledge',
            },
        ),
    ]
