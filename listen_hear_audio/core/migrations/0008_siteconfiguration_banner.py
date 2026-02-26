from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_brandpartner"),
    ]

    operations = [
        migrations.AddField(
            model_name="siteconfiguration",
            name="banner_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Show a site-wide announcement banner at the top of every page",
            ),
        ),
        migrations.AddField(
            model_name="siteconfiguration",
            name="banner_text",
            field=models.TextField(
                blank=True,
                help_text="Text to display in the banner (plain text only)",
            ),
        ),
    ]
