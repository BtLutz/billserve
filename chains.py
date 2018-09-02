from celery import chain, signature
import celery


class RelatedBillChain:
    @staticmethod
    def execute(related_bill_url, current_bill_pk):
        pb_task_name = 'billserve.tasks.populate_bill'
        arb_signature = signature('billserve.tasks.add_related_bill', args=[current_bill_pk])
        celery.current_app.send_task(pb_task_name, args=[related_bill_url], link=arb_signature)
