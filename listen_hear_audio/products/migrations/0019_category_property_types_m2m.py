"""
Migration: Replace Category.property_type ForeignKey with property_types ManyToManyField.

Steps:
  1. Drop the unique_together constraint FIRST (while property_type still exists).
  2. Add the new M2M field with a temporary related_name to avoid clashing with the FK.
  3. Data migration: copy the existing FK value into the M2M for every category.
  4. Remove the old FK field.
  5. Switch the M2M related_name to 'categories' now that the FK is gone.
  6. Make slug globally unique.
"""

from django.db import migrations, models


def copy_fk_to_m2m(apps, schema_editor):
    """Populate the new M2M table from the existing FK column."""
    Category = apps.get_model('products', 'Category')
    for cat in Category.objects.all():
        if cat.property_type_id:
            cat.property_types.add(cat.property_type_id)


def reverse_m2m_to_fk(apps, schema_editor):
    """Restore the FK from the first M2M entry when reversing the migration."""
    Category = apps.get_model('products', 'Category')
    for cat in Category.objects.prefetch_related('property_types'):
        pt = cat.property_types.first()
        if pt:
            cat.property_type_id = pt.pk
            cat.save(update_fields=['property_type_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0018_remove_package_catalog_only_package_visibility'),
    ]

    operations = [
        # 1. Drop unique_together FIRST — must happen while property_type field still exists.
        migrations.AlterUniqueTogether(
            name='category',
            unique_together=set(),
        ),

        # 2. Add M2M with a temp related_name so it doesn't clash with the existing FK
        #    (both would otherwise claim related_name='categories' on PropertyType).
        migrations.AddField(
            model_name='category',
            name='property_types',
            field=models.ManyToManyField(
                blank=True,
                related_name='categories_new',
                to='products.propertytype',
            ),
        ),

        # 3. Seed the M2M from the existing FK values.
        migrations.RunPython(copy_fk_to_m2m, reverse_code=reverse_m2m_to_fk),

        # 4. Drop the old FK field (releases related_name='categories').
        migrations.RemoveField(
            model_name='category',
            name='property_type',
        ),

        # 5. Now that FK is gone, rename related_name to the canonical 'categories'.
        migrations.AlterField(
            model_name='category',
            name='property_types',
            field=models.ManyToManyField(
                blank=True,
                help_text='Select all property types this category applies to (e.g., Residential, Commercial)',
                related_name='categories',
                to='products.propertytype',
            ),
        ),

        # 6. Make slug globally unique (previously only unique per property_type).
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(blank=True, max_length=200, unique=True),
        ),
    ]
