from __future__ import absolute_import

from django.utils.translation import ugettext_lazy as _
from django.db.models import Avg, Count, Min, Max

from common.utils import pretty_size, pretty_size_10

from .conf.settings import STORAGE_BACKEND
from .models import Document, DocumentType, DocumentPage, DocumentVersion


def get_used_size(path, file_list):
    total_size = 0
    for filename in file_list:
        try:
            total_size += STORAGE_BACKEND().size(STORAGE_BACKEND.separator.join([path, filename]))
        except OSError:
            pass

    return total_size


def storage_count(path=u'.'):
    directories, files = STORAGE_BACKEND().listdir(path)
    total_count = len(files)
    total_size = get_used_size(path, files)

    for directory in directories:
        file_count, files_size = storage_count(directory)
        total_count += file_count
        total_size += files_size

    return total_count, total_size


def get_statistics():
    total_db_documents = Document.objects.only('pk',).count()

    paragraphs = [
        _(u'Document types: %d') % DocumentType.objects.count(),
        _(u'Documents in database: %d') % total_db_documents,
    ]

    try:
        total_storage_documents, storage_used_space = storage_count()
        paragraphs.append(_(u'Documents in storage: %d') %
            total_storage_documents)
        paragraphs.append(_(u'Space used in storage: %(base_2)s (base 2), %(base_10)s (base 10), %(bytes)d bytes') % {
            'base_2': pretty_size(storage_used_space),
            'base_10': pretty_size_10(storage_used_space),
            'bytes': storage_used_space
        })
    except NotImplementedError:
        pass

    paragraphs.extend(
        [
            _(u'Document pages in database: %d') % DocumentPage.objects.only('pk',).count(),
            _(u'Minimum amount of pages per document: %(page_count__min)d') % DocumentVersion.objects.annotate(page_count=Count('documentpage')).aggregate(Min('page_count')),
            _(u'Maximum amount of pages per document: %(page_count__max)d') % DocumentVersion.objects.annotate(page_count=Count('documentpage')).aggregate(Max('page_count')),
            _(u'Average amount of pages per document: %(page_count__avg)f') % DocumentVersion.objects.annotate(page_count=Count('documentpage')).aggregate(Avg('page_count')),
        ]
    )
    #[(day_count['date_added'].strftime('%Y-%m-%d'), day_count['id__count']) for day_count in Document.objects.values('date_added').annotate(Count("id"))]

    return {
        'title': _(u'Document statistics'),
        'paragraphs': paragraphs
    }
