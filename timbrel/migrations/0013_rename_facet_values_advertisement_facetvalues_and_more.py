# Generated by Django 5.1.1 on 2024-12-09 05:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0012_facetvalue_tags'),
    ]

    operations = [
        migrations.RenameField(
            model_name='advertisement',
            old_name='facet_values',
            new_name='facetvalues',
        ),
        migrations.RenameField(
            model_name='article',
            old_name='facet_values',
            new_name='facetvalues',
        ),
        migrations.RenameField(
            model_name='articleimage',
            old_name='facet_values',
            new_name='facetvalues',
        ),
        migrations.RenameField(
            model_name='articletext',
            old_name='facet_values',
            new_name='facetvalues',
        ),
        migrations.RenameField(
            model_name='file',
            old_name='facet_values',
            new_name='facetvalues',
        ),
        migrations.RenameField(
            model_name='setting',
            old_name='facet_values',
            new_name='facetvalues',
        ),
        migrations.RenameField(
            model_name='tag',
            old_name='facet_values',
            new_name='facetvalues',
        ),
        migrations.AlterField(
            model_name='facetvalue',
            name='facet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='facetvalues', to='common.facet'),
        ),
    ]