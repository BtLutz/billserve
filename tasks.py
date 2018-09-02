from __future__ import absolute_import, unicode_literals
from celery import shared_task

from billserve.networking.client import GovinfoClient
from billserve.models import Bill


@shared_task
def add_related_bill(related_bill_pk, bill_pk):
    related_bill = Bill.objects.get(pk=related_bill_pk)
    bill = Bill.objects.get(pk=bill_pk)

    related_bill.related_bills.add(bill)
    related_bill.save()

    bill.related_bills.add(related_bill)
    bill.save()


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
