from __future__ import absolute_import, unicode_literals
from celery import shared_task

from billserve.networking.client import GovinfoClient


@shared_task
def add_related_bill(current_bill_pk, related_bill_pk):
    """
    Ties bills together by adding each to the other's related bills.
    :param current_bill_pk: The primary key of the first related bill
    :param related_bill_pk: The primary key of the second related bill
    """
    from .models import Bill

    Bill.objects.add_related_bill(current_bill_pk, related_bill_pk)


@shared_task
def populate_bill(url):
    """
    Either gets an existing bill from the database or creates a new one based on its URL
    :param url: A URL pointing towards a valid GovInfo endpoint
    :return: The primary key of the bill we've either gotten or created
    """
    from .models import Bill

    try:
        bill = Bill.objects.get(bill_url=url)
    except Bill.DoesNotExist:
        bill = GovinfoClient.create_bill_from_url(url)

    return bill.pk


@shared_task
def update(origin_url):
    """
    Currently starts at a single bill URL and then spiders out from there. Eventually this method will query all
    possible bill repositories and see if there are any new bills to grab.
    :param origin_url: The URL to begin our search at
    """
    populate_bill.delay(origin_url)


@shared_task
def rebuild():
    """
    Destroys and then rebuilds all the legislative support splits.
    """
    from .models import LegislativeSubjectSupportSplit

    LegislativeSubjectSupportSplit.objects.rebuild()


