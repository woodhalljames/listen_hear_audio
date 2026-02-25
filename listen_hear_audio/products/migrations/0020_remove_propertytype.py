"""
Migration: Remove property_types ManyToManyField from Category and delete the PropertyType model.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0019_category_property_types_m2m'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='property_types',
        ),
        migrations.DeleteModel(
            name='PropertyType',
        ),
    ]
