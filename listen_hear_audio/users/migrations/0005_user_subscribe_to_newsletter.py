from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_user_phone_user_website"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="subscribe_to_newsletter",
            field=models.BooleanField(
                default=False,
                help_text="User opted in to receive marketing and newsletter emails.",
            ),
        ),
    ]
