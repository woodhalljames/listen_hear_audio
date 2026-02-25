from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogpost',
            name='notified_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Set automatically when subscribers are notified. Prevents duplicate sends.'
            ),
        ),
    ]
