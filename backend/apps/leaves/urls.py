from django.urls import path
from .views import (
    LeaveBalanceListView, LeaveApplyView, LeaveRequestListView, LeaveRequestDetailView,
    PendingApprovalsView, LeaveApproveView, LeaveRejectView,
    LeaveTypeListView, LeaveTypeCreateView, LeaveTypeUpdateView
)

urlpatterns = [
    path('', LeaveRequestListView.as_view(), name='leave_request_list'),
    path('apply/', LeaveApplyView.as_view(), name='leave_apply'),
    path('balances/', LeaveBalanceListView.as_view(), name='leave_balance_list'),
    path('pending/', PendingApprovalsView.as_view(), name='pending_approvals'),
    path('<int:pk>/', LeaveRequestDetailView.as_view(), name='leave_request_detail'),
    path('<int:pk>/approve/', LeaveApproveView.as_view(), name='leave_approve'),
    path('<int:pk>/reject/', LeaveRejectView.as_view(), name='leave_reject'),

    # Leave Type Configuration (HR & Admin)
    path('types/', LeaveTypeListView.as_view(), name='leave_type_list'),
    path('types/create/', LeaveTypeCreateView.as_view(), name='leave_type_create'),
    path('types/<int:pk>/edit/', LeaveTypeUpdateView.as_view(), name='leave_type_edit'),
]
