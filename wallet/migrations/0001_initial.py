# Generated by Django 2.0.2 on 2018-03-04 14:25

from django.db import migrations, models
import django.db.models.deletion
import django_countries.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abrev', models.CharField(max_length=3, unique=True)),
                ('name', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=20)),
                ('last_name', models.CharField(max_length=20)),
                ('password', models.CharField(max_length=32)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('birthday', models.DateField()),
                ('address', models.CharField(blank=True, max_length=52, null=True)),
                ('phone', models.CharField(blank=True, max_length=11, null=True)),
                ('gender', models.CharField(choices=[('H', 'HOMBRE'), ('M', 'MUJER'), ('D', 'OTRO')], default='D', max_length=2)),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('last_update', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('address', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('public_key', models.CharField(max_length=64, unique=True)),
                ('private_key', models.CharField(max_length=64, unique=True)),
                ('balance', models.DecimalField(decimal_places=8, default=0, max_digits=18)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wallet.Currency')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wallet.User')),
            ],
        ),
    ]
