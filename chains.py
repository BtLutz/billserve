from celery import chain, signature
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
