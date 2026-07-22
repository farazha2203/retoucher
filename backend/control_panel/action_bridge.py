from rest_framework.test import APIRequestFactory, force_authenticate

from orders.views import OrderViewSet
from projects.views import ProjectRequestViewSet


ORDER_ACTION_METHODS = {
    "submit": "submit",
    "upload_image": "upload_image",
    "start_review": "start_review",
    "assign_editor": "assign_editor",
    "start_work": "start_work",
    "deliver": "deliver",
    "supervisor_approve": "supervisor_approve",
    "supervisor_request_revision": "supervisor_request_revision",
    "client_approve": "client_approve",
    "client_request_revision": "client_request_revision",
    "supervisor_accept_client_revision": "supervisor_accept_client_revision",
    "supervisor_reject_client_revision": "supervisor_reject_client_revision",
    "start_revision": "start_revision",
}

PROJECT_ACTION_METHODS = {
    "upload_image": "upload_image",
    "direct_proposal": "direct_proposal",
    "direct_decline": "direct_decline",
    "public_proposal": "public_proposal",
    "sample_proposal": "sample_proposal",
    "convert_to_order": "convert_to_order",
    "managed_assign": "managed_assign",
}


def _payload(post, files):
    data = {}
    for key in post:
        if key == "csrfmiddlewaretoken":
            continue
        values = post.getlist(key)
        data[key] = values if len(values) > 1 else post.get(key)
    for key in files:
        values = files.getlist(key)
        data[key] = values if len(values) > 1 else files.get(key)
    return data


def invoke_order_action(request, pk, action_key):
    method = ORDER_ACTION_METHODS[action_key]
    factory = APIRequestFactory()
    api_request = factory.post(
        f"/api/orders/{pk}/{action_key}/",
        _payload(request.POST, request.FILES),
        format="multipart" if request.FILES else "json",
    )
    force_authenticate(api_request, user=request.user)
    view = OrderViewSet.as_view({"post": method})
    response = view(api_request, pk=str(pk))
    response.render()
    return response


def invoke_project_action(request, pk, action_key):
    method = PROJECT_ACTION_METHODS[action_key]
    factory = APIRequestFactory()
    api_request = factory.post(
        f"/api/projects/{pk}/{action_key}/",
        _payload(request.POST, request.FILES),
        format="multipart" if request.FILES else "json",
    )
    force_authenticate(api_request, user=request.user)
    view = ProjectRequestViewSet.as_view({"post": method})
    response = view(api_request, pk=str(pk))
    response.render()
    return response



def invoke_project_proposal_action(
    request,
    *,
    project_pk,
    proposal_pk,
    method_name,
):
    factory = APIRequestFactory()
    api_request = factory.post(
        (
            f"/api/projects/requests/{project_pk}/"
            f"proposals/{proposal_pk}/{method_name}/"
        ),
        _payload(request.POST, request.FILES),
        format="multipart" if request.FILES else "json",
    )
    force_authenticate(api_request, user=request.user)
    view = ProjectRequestViewSet.as_view({"post": method_name})
    response = view(
        api_request,
        pk=str(project_pk),
        proposal_id=str(proposal_pk),
    )
    response.render()
    return response
