from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0003_newsletter_subscribers'),
    ]

    operations = [
        migrations.AddField(
            model_name='testimonial',
            name='photo',
            field=models.BinaryField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='testimonial',
            name='photo_content_type',
            field=models.CharField(blank=True, editable=False, max_length=40),
        ),
    ]
