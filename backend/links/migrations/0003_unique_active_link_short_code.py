from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('links', '0002_alter_link_short_code'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='link',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_deleted=False),
                fields=('short_code',),
                name='unique_active_link_short_code',
            ),
        ),
    ]
