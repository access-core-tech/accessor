from fast_grpc import FastGRPC

from server.views.access_requests import access_request_view
from server.views.access_accounts import resource_access_accounts_view
from server.views.resources import resource_view
from server.views.revoke_access import revoke_requests_view

app = FastGRPC(name="AccessorService", auto_gen_proto=False)

app.unary_unary()(resource_view.get_resource)
app.unary_unary()(resource_view.get_resources)
app.unary_unary()(resource_view.create_resource)
app.unary_unary()(resource_view.update_resource)
app.unary_unary()(resource_view.delete_resource)

app.unary_unary()(access_request_view.get_access_request)
app.unary_unary()(access_request_view.get_accesses_request)
app.unary_unary()(access_request_view.create_access_request)
app.unary_unary()(access_request_view.approve_access)
app.unary_unary()(access_request_view.deny_access)

app.unary_unary()(resource_access_accounts_view.get_resource_access_account)
app.unary_unary()(resource_access_accounts_view.get_resources_access_accounts)

app.unary_unary()(revoke_requests_view.get_revoke)
app.unary_unary()(revoke_requests_view.get_revokes)
app.unary_unary()(revoke_requests_view.revoke_access)
