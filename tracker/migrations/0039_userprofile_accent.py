from django.db import migrations, models


TABLE = 'tracker_userprofile'


def _column_exists(schema_editor, column):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s",
            [TABLE, column],
        )
        return cursor.fetchone()[0] > 0


def add_accent_column(apps, schema_editor):
    # La colonna 'accent' puo' gia' esistere fisicamente (residuo del tentativo
    # precedente di sistema temi, mai droppato su alcuni database) anche se il
    # modello Django non la conosceva piu': qui la aggiungiamo solo se manca
    # davvero, cosi' la migrazione funziona sia su chi ce l'ha gia' sia su chi no.
    if not _column_exists(schema_editor, 'accent'):
        schema_editor.execute(
            f"ALTER TABLE {TABLE} ADD COLUMN accent VARCHAR(20) NOT NULL DEFAULT 'viola'"
        )


def remove_accent_column(apps, schema_editor):
    if _column_exists(schema_editor, 'accent'):
        schema_editor.execute(f"ALTER TABLE {TABLE} DROP COLUMN accent")


def drop_tema_column(apps, schema_editor):
    # 'tema' e' un altro residuo dello stesso tentativo (mai riadottato nel
    # modello: il tema chiaro/scuro e' rimandato). Va rimossa perche' essendo
    # NOT NULL senza default a livello di database blocca la creazione di
    # nuovi UserProfile con un IntegrityError.
    if _column_exists(schema_editor, 'tema'):
        schema_editor.execute(f"ALTER TABLE {TABLE} DROP COLUMN tema")


def readd_tema_column_noop(apps, schema_editor):
    # Nessun ripristino: la colonna non e' piu' usata da nessun codice.
    pass


class Migration(migrations.Migration):

    # MySQL non supporta DDL transazionale: piu' ALTER TABLE nella stessa
    # transazione fanno scattare un commit implicito che confonde il
    # tracking delle transazioni di Django (TransactionManagementError).
    atomic = False

    dependencies = [
        ('tracker', '0038_sleepentry'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='userprofile',
                    name='accent',
                    field=models.CharField(
                        choices=[
                            ('viola', 'Viola'),
                            ('corallo', 'Corallo'),
                            ('lime', 'Lime'),
                            ('teal', 'Teal'),
                            ('verde', 'Verde'),
                        ],
                        default='viola',
                        max_length=20,
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_accent_column, remove_accent_column),
            ],
        ),
        migrations.RunPython(drop_tema_column, readd_tema_column_noop),
    ]
