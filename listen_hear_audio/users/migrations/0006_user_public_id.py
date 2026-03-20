import uuid

from django.db import migrations, models


def populate_public_ids(apps, schema_editor):
    User = apps.get_model("users", "User")
    for user in User.objects.filter(public_id__isnull=True):
        user.public_id = uuid.uuid4()
        user.save(update_fields=["public_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_user_subscribe_to_newsletter"),
    ]

    operations = [
        # Step 1: add nullable, no unique constraint yet
        migrations.AddField(
            model_name="user",
            name="public_id",
            field=models.UUIDField(null=True, editable=False),
        ),
        # Step 2: fill a unique UUID for every existing row
        migrations.RunPython(populate_public_ids, migrations.RunPython.noop),
        # Step 3: make it non-nullable and unique
        migrations.AlterField(
            model_name="user",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
