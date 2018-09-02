from __future__ import absolute_import, unicode_literals
from celery import shared_task

from billserve.networking.client import GovinfoClient
from billserve.models import Bill, BillManager


@shared_task
def add_related_bill(current_bill_pk, related_bill_pk):
    BillManager.add_related_bill(current_bill_pk, related_bill_pk)


@shared_task
def populate_bill(url):
    try:
        bill = Bill.objects.get(bill_url=url)
    except Bill.DoesNotExist:
        bill = GovinfoClient.create_bill_from_url(url)

    return bill.pk


@shared_task
def update(origin_url):
    populate_bill.delay(origin_url)
