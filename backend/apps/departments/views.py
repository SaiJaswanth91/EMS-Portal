from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q, Count
from apps.accounts.mixins import RoleRequiredMixin
from .models import Department, Designation
from .forms import DepartmentForm, DesignationForm


class DepartmentListView(LoginRequiredMixin, ListView):
    """List departments with search, filtering, and designation counts."""
    model = Department
    template_name = 'departments/department_list.html'
    context_object_name = 'departments'
    paginate_by = 10

    def get_queryset(self):
        queryset = Department.objects.annotate(designation_count=Count('designations')).order_by('name')
        search_query = self.request.GET.get('q')
        status_filter = self.request.GET.get('status')

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(code__icontains=search_query)
            )
        if status_filter in ['true', 'false']:
            queryset = queryset.filter(status=(status_filter == 'true'))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['total_departments'] = Department.objects.count()
        context['active_departments'] = Department.objects.filter(status=True).count()
        return context


class DepartmentCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ['ADMIN', 'HR']
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    success_url = reverse_lazy('department_list')

    def form_valid(self, form):
        messages.success(self.request, f"Department '{form.instance.name}' created successfully!")
        return super().form_valid(form)


class DepartmentUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ['ADMIN', 'HR']
    model = Department
    form_class = DepartmentForm
    template_name = 'departments/department_form.html'
    success_url = reverse_lazy('department_list')

    def form_valid(self, form):
        messages.success(self.request, f"Department '{form.instance.name}' updated successfully!")
        return super().form_valid(form)


class DepartmentDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ['ADMIN', 'HR']
    model = Department
    template_name = 'departments/department_confirm_delete.html'
    success_url = reverse_lazy('department_list')

    def form_valid(self, form):
        messages.success(self.request, f"Department '{self.object.name}' deleted successfully!")
        return super().form_valid(form)


class DepartmentToggleStatusView(RoleRequiredMixin, View):
    allowed_roles = ['ADMIN', 'HR']

    def post(self, request, pk):
        department = get_object_or_404(Department, pk=pk)
        department.status = not department.status
        department.save()
        status_str = "activated" if department.status else "deactivated"
        messages.success(request, f"Department '{department.name}' has been {status_str}.")
        return redirect('department_list')


class DesignationListView(LoginRequiredMixin, ListView):
    """List designations with department filters."""
    model = Designation
    template_name = 'departments/designation_list.html'
    context_object_name = 'designations'
    paginate_by = 12

    def get_queryset(self):
        queryset = Designation.objects.select_related('department').order_by('name')
        search_query = self.request.GET.get('q')
        dept_filter = self.request.GET.get('department')

        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
        if dept_filter:
            queryset = queryset.filter(department_id=dept_filter)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departments'] = Department.objects.filter(status=True)
        context['search_query'] = self.request.GET.get('q', '')
        context['dept_filter'] = self.request.GET.get('department', '')
        return context


class DesignationCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ['ADMIN', 'HR']
    model = Designation
    form_class = DesignationForm
    template_name = 'departments/designation_form.html'
    success_url = reverse_lazy('designation_list')

    def form_valid(self, form):
        messages.success(self.request, f"Designation '{form.instance.name}' created successfully!")
        return super().form_valid(form)


class DesignationUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ['ADMIN', 'HR']
    model = Designation
    form_class = DesignationForm
    template_name = 'departments/designation_form.html'
    success_url = reverse_lazy('designation_list')

    def form_valid(self, form):
        messages.success(self.request, f"Designation '{form.instance.name}' updated successfully!")
        return super().form_valid(form)


class DesignationDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ['ADMIN', 'HR']
    model = Designation
    template_name = 'departments/designation_confirm_delete.html'
    success_url = reverse_lazy('designation_list')

    def form_valid(self, form):
        messages.success(self.request, f"Designation '{self.object.name}' deleted successfully!")
        return super().form_valid(form)
