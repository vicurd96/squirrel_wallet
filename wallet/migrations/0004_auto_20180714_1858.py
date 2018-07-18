# Generated by Django 2.0.5 on 2018-07-14 22:58

from django.db import migrations, models
import wallet.helpers


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0003_auto_20180714_1729'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='avatar',
            field=models.ImageField(default='content/avatar/None/no-img.jpg', upload_to=wallet.helpers.RandomFileName('content/avatar')),
        ),
    ]
