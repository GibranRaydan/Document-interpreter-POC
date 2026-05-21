from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from courtney.models import Book
from courtney.temporal_dispatch import start_book_workflow


class Command(BaseCommand):
    help = "Dispara el BookWorkflow para procesar un libro entero desde un directorio local."

    def add_arguments(self, parser):
        parser.add_argument("folder_path", type=str, help="Ruta absoluta al directorio del libro")

    def handle(self, *args, folder_path: str, **kwargs):
        path = Path(folder_path).expanduser().resolve()
        if not path.exists():
            raise CommandError(f"La ruta no existe: {path}")
        if not path.is_dir():
            raise CommandError(f"La ruta no es un directorio: {path}")

        book, created = Book.objects.get_or_create(
            folder_path=str(path),
            defaults={"name": path.name},
        )
        verb = "creado" if created else "reanudado"
        self.stdout.write(self.style.NOTICE(f"Book {book.uuid} {verb} (path={path})"))

        start_book_workflow(book.pk, str(book.uuid), str(path))
        self.stdout.write(self.style.SUCCESS(
            f"BookWorkflow disparado. Consulta estado en: GET /api/v1/books/{book.uuid}/"
        ))
