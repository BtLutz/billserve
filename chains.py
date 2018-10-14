from celery import signature
from .tasks import update, rebuild
import celery


class RelatedBillChain:
    @staticmethod
    def execute(related_bill_url, current_bill_pk):
        """
        Executes the asynchronous task chain we need to make a related bill and get it added
        to its sibling bill correctly.
        :param related_bill_url: The URL of the related bill we'd like to parse. May or may not exist in database.
        :param current_bill_pk: The primary key of the bill we've already parsed. Exists in database.
        """
        pb_task_name = 'billserve.tasks.populate_bill'
        arb_signature = signature('billserve.tasks.add_related_bill', args=[current_bill_pk])
        celery.current_app.send_task(pb_task_name, args=[related_bill_url], link=arb_signature)


class UpdateChain:
    @staticmethod
    def execute(url):
        """
        Executes the asynchronous task chain we need to update the bill database and then rebuild support splits.
        :param url: The URL to start our graph search at
        """
        update.apply_async((url,), link=rebuild.s())
