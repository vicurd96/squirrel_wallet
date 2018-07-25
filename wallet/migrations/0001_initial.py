# Generated by Django 2.0.7 on 2018-07-19 13:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_countries.fields
import fernet_fields.fields
import uuid
import wallet.helpers
import wallet.models
import wallet.storage


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('first_name', models.CharField(max_length=20, verbose_name='First name')),
                ('last_name', models.CharField(max_length=20, verbose_name='Last name')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'db_table': 'users',
            },
            managers=[
                ('objects', wallet.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('abrev', models.CharField(max_length=3, unique=True)),
                ('name', models.CharField(max_length=20)),
                ('api', models.CharField(max_length=255, null=True)),
            ],
            options={
                'db_table': 'currencies',
            },
        ),
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('password', 'Password change'), ('update', 'Updated profile'), ('security', '2-pass authenticator configured'), ('TX', 'Cryptocurrency transaction')], max_length=8, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'operations',
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(default='static/avatar/None/no-img.jpg', storage=wallet.storage.OverwriteStorage(), upload_to=wallet.helpers.RandomFileName('static/avatar'))),
                ('birthdate', models.DateField(blank=True, null=True, verbose_name='Birthdate')),
                ('address', models.CharField(blank=True, max_length=52, null=True, verbose_name='Address')),
                ('phone', models.CharField(blank=True, max_length=11, null=True, verbose_name='Number phone')),
                ('gender', models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Unknown', 'Unknown')], default='Unknown', max_length=7, null=True, verbose_name='Gender')),
                ('country', django_countries.fields.CountryField(max_length=2, null=True, verbose_name='Country')),
                ('last_update', models.DateTimeField(auto_now=True, verbose_name='Last update')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'profiles',
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('txid', models.CharField(max_length=255, null=True, verbose_name='TXID')),
                ('to', models.CharField(max_length=64, verbose_name='To address')),
                ('status', models.NullBooleanField(default=False, verbose_name='Status')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('type', models.CharField(choices=[('IN', 'IN'), ('OUT', 'OUT')], default='OUT', max_length=3, verbose_name='Type')),
                ('amount', models.DecimalField(decimal_places=8, max_digits=16, null=True, verbose_name='Amount')),
                ('fee', models.DecimalField(decimal_places=8, max_digits=16, null=True, verbose_name='Fee')),
            ],
            options={
                'db_table': 'transactions',
            },
        ),
        migrations.CreateModel(
            name='Value',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('value', models.DecimalField(decimal_places=4, default=0, max_digits=16)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='wallet.Currency')),
            ],
            options={
                'db_table': 'values',
            },
        ),
        migrations.CreateModel(
            name='Wallet',
            fields=[
                ('address', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('private_key', fernet_fields.fields.EncryptedCharField(max_length=64)),
                ('balance', models.DecimalField(decimal_places=8, default=0, max_digits=16, verbose_name='Balance')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created at')),
                ('last_update', models.DateTimeField(verbose_name='Last update')),
                ('qrcode', models.ImageField(blank=True, null=True, upload_to='static/qrcode', verbose_name='QR Code')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='wallet.Currency')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'wallets',
            },
            managers=[
                ('objects', wallet.models.WalletManager()),
            ],
        ),
        migrations.AddField(
            model_name='transaction',
            name='wallet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='wallet.Wallet'),
        ),
    ]
