# Generated by Django 3.0.5 on 2020-05-05 05:14

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Stocks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=200)),
                ('name', models.CharField(max_length=200)),
                ('price', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('change', models.DecimalField(decimal_places=2, max_digits=10)),
                ('stocks_owned', models.IntegerField()),
                ('buying_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('balance', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
    ]
