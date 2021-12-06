# Generated by Django 3.2.9 on 2021-12-06 22:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Benefit',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('field', models.CharField(blank=True, default='', max_length=30)),
                ('title', models.CharField(blank=True, default='', max_length=100)),
                ('contents', models.TextField(blank=True, default='')),
                ('who', models.TextField(blank=True, default='')),
                ('howTo', models.TextField(blank=True, default='')),
            ],
        ),
    ]
