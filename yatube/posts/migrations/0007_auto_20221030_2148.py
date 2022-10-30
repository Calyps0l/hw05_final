# Generated by Django 2.2.16 on 2022-10-30 18:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_follow'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='unique_follower'),
        ),
    ]