# Generated by Django 2.0.13 on 2019-09-11 06:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trello', '0002_auto_20190911_1354'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cardimage',
            old_name='card_img',
            new_name='image',
        ),
    ]
