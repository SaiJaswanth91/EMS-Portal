from django.urls import path
from .views import (
    DepartmentListView, DepartmentCreateView, DepartmentUpdateView, DepartmentDeleteView, DepartmentToggleStatusView,
    DesignationListView, DesignationCreateView, DesignationUpdateView, DesignationDeleteView
)

urlpatterns = [
    path('', DepartmentListView.as_view(), name='department_list'),
    path('create/', DepartmentCreateView.as_view(), name='department_create'),
    path('<int:pk>/edit/', DepartmentUpdateView.as_view(), name='department_edit'),
    path('<int:pk>/delete/', DepartmentDeleteView.as_view(), name='department_delete'),
    path('<int:pk>/toggle-status/', DepartmentToggleStatusView.as_view(), name='department_toggle_status'),

    path('designations/', DesignationListView.as_view(), name='designation_list'),
    path('designations/create/', DesignationCreateView.as_view(), name='designation_create'),
    path('designations/<int:pk>/edit/', DesignationUpdateView.as_view(), name='designation_edit'),
    path('designations/<int:pk>/delete/', DesignationDeleteView.as_view(), name='designation_delete'),
]
