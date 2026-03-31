from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exams', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Badge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('icon_emoji', models.CharField(max_length=10)),
                ('badge_type', models.CharField(choices=[('achievement', 'Achievement'), ('milestone', 'Meilenstein'), ('skill', 'Fähigkeit')], default='achievement', max_length=20)),
                ('condition', models.TextField(help_text='Bedingung für Badge (z.B. \'5_courses_completed\')')),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_xp', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to='auth.user')),
            ],
            options={
                'ordering': ['-total_xp'],
            },
        ),
        migrations.AlterField(
            model_name='result',
            name='score',
            field=models.IntegerField(),
        ),
        migrations.AddField(
            model_name='result',
            name='total_questions',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='result',
            name='xp_earned',
            field=models.IntegerField(default=0, help_text='XP die bei diesem Quiz verdient wurden'),
        ),
        migrations.CreateModel(
            name='UserBadge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('earned_at', models.DateTimeField(auto_now_add=True)),
                ('badge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exams.badge')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='badges', to='auth.user')),
            ],
            options={
                'ordering': ['-earned_at'],
                'unique_together': {('user', 'badge')},
            },
        ),
    ]
