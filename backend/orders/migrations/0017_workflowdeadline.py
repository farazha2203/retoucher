from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[("projects","0008_remove_projectrequestimage_expires_at_and_more"),("orders","0016_dispute_disputeevidence_disputemessage"),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[migrations.CreateModel(name="WorkflowDeadline",fields=[
      ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
      ("stage",models.CharField(max_length=64)),("owner_role",models.CharField(blank=True,max_length=32)),
      ("due_at",models.DateTimeField()),("grace_period_minutes",models.PositiveIntegerField(default=0)),
      ("timeout_action",models.CharField(default="notify",max_length=64)),
      ("status",models.CharField(choices=[("active","Active"),("met","Met"),("missed","Missed"),("cancelled","Cancelled")],default="active",max_length=16)),
      ("met_at",models.DateTimeField(blank=True,null=True)),("missed_at",models.DateTimeField(blank=True,null=True)),("cancelled_at",models.DateTimeField(blank=True,null=True)),
      ("metadata",models.JSONField(blank=True,default=dict)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True)),
      ("order",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.CASCADE,related_name="workflow_deadlines",to="orders.order")),
      ("project_request",models.ForeignKey(blank=True,null=True,on_delete=django.db.models.deletion.CASCADE,related_name="workflow_deadlines",to="projects.projectrequest")),
    ],options={"ordering":("-created_at",)}),
    migrations.AddConstraint(model_name="workflowdeadline",constraint=models.CheckConstraint(condition=(models.Q(("order__isnull",False),("project_request__isnull",True))|models.Q(("order__isnull",True),("project_request__isnull",False))),name="workflow_deadline_exactly_one_target")),
    migrations.AddIndex(model_name="workflowdeadline",index=models.Index(fields=["status","due_at"],name="orders_work_status_1dd769_idx")),
    migrations.AddIndex(model_name="workflowdeadline",index=models.Index(fields=["order","status"],name="orders_work_order_i_b3e739_idx")),
    migrations.AddIndex(model_name="workflowdeadline",index=models.Index(fields=["project_request","status"],name="orders_work_project_0fb75a_idx")),
 ]
