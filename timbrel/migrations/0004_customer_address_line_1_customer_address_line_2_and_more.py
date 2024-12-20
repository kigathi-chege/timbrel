# Generated by Django 5.1.4 on 2024-12-21 11:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cities_light', '0011_alter_city_country_alter_city_region_and_more'),
        ('timbrel', '0003_historicalpaymentmethod_payment_method_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='address_line_1',
            field=models.CharField(blank=True, db_comment='The main address line (house/building number, street name).', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='address_line_2',
            field=models.CharField(blank=True, db_comment='Optional field for additional address details (e.g., apartment number, suite, floor).', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='billing_cycle',
            field=models.CharField(blank=True, choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('semi_annually', 'Semi Annually'), ('annually', 'Annually')], max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='city',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='cities_light.city'),
        ),
        migrations.AddField(
            model_name='customer',
            name='company_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='delivery_instructions',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='is_primary',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customer',
            name='payment_method',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='timbrel.paymentmethod'),
        ),
        migrations.AddField(
            model_name='customer',
            name='phone',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='postal_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='subregion',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='cities_light.subregion'),
        ),
        migrations.AddField(
            model_name='customer',
            name='vat_number',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='address_line_1',
            field=models.CharField(blank=True, db_comment='The main address line (house/building number, street name).', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='address_line_2',
            field=models.CharField(blank=True, db_comment='Optional field for additional address details (e.g., apartment number, suite, floor).', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='billing_cycle',
            field=models.CharField(blank=True, choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('semi_annually', 'Semi Annually'), ('annually', 'Annually')], max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='city',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='cities_light.city'),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='company_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='delivery_instructions',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='is_primary',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='payment_method',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='timbrel.paymentmethod'),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='phone',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='postal_code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='subregion',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='cities_light.subregion'),
        ),
        migrations.AddField(
            model_name='historicalcustomer',
            name='vat_number',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
