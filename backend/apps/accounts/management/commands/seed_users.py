from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.departments.models import Department, Designation
from apps.employees.models import Employee, EmploymentType, EmploymentStatus
from apps.leaves.models import LeaveType, LeavePolicy, LeaveBalance

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds initial development users, departments, designations, employee profiles, leave types, policies, and balances.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Seeding development data...'))

        # 1. Seed Users
        users_data = [
            {'email': 'admin@eelms.com', 'password': 'Admin@123', 'first_name': 'System', 'last_name': 'Administrator', 'role': User.Role.ADMIN, 'is_staff': True, 'is_superuser': True},
            {'email': 'hr@eelms.com', 'password': 'Hr@123', 'first_name': 'Sarah', 'last_name': 'Jenkins', 'role': User.Role.HR, 'is_staff': True, 'is_superuser': False},
            {'email': 'manager1@eelms.com', 'password': 'Manager@123', 'first_name': 'David', 'last_name': 'Miller', 'role': User.Role.MANAGER, 'is_staff': False, 'is_superuser': False},
            {'email': 'manager2@eelms.com', 'password': 'Manager@123', 'first_name': 'Emily', 'last_name': 'Watson', 'role': User.Role.MANAGER, 'is_staff': False, 'is_superuser': False},
            {'email': 'employee1@eelms.com', 'password': 'Employee@123', 'first_name': 'Alex', 'last_name': 'Rivera', 'role': User.Role.EMPLOYEE, 'is_staff': False, 'is_superuser': False},
            {'email': 'employee2@eelms.com', 'password': 'Employee@123', 'first_name': 'Jessica', 'last_name': 'Taylor', 'role': User.Role.EMPLOYEE, 'is_staff': False, 'is_superuser': False},
        ]

        created_users = {}
        for user_info in users_data:
            email = user_info.pop('email')
            password = user_info.pop('password')
            user, _ = User.objects.get_or_create(email=email, defaults=user_info)
            user.set_password(password)
            user.is_verified = True
            user.is_active = True
            for key, value in user_info.items():
                setattr(user, key, value)
            user.save()
            created_users[email] = user

        self.stdout.write(self.style.SUCCESS(f"Users seeded: {len(created_users)}"))

        # 2. Seed Departments
        dept_data = [
            {'code': 'TECH', 'name': 'Engineering & Technology', 'description': 'Software development, DevOps, IT operations.', 'head_email': 'manager1@eelms.com'},
            {'code': 'HR', 'name': 'Human Resources', 'description': 'Talent acquisition, leave policies, employee relations.', 'head_email': 'hr@eelms.com'},
            {'code': 'FIN', 'name': 'Finance & Accounting', 'description': 'Payroll, auditing, financial reporting.', 'head_email': 'manager2@eelms.com'},
            {'code': 'MKT', 'name': 'Marketing & Sales', 'description': 'Product marketing, client relations, lead growth.', 'head_email': None},
        ]

        created_depts = {}
        for d in dept_data:
            head = created_users.get(d['head_email']) if d['head_email'] else None
            dept, _ = Department.objects.get_or_create(
                code=d['code'],
                defaults={'name': d['name'], 'description': d['description'], 'department_head': head, 'status': True}
            )
            dept.department_head = head
            dept.save()
            created_depts[d['code']] = dept

        self.stdout.write(self.style.SUCCESS(f"Departments seeded: {len(created_depts)}"))

        # 3. Seed Designations
        desig_data = [
            {'name': 'Software Developer', 'dept_code': 'TECH', 'desc': 'Develops core web services and UI.'},
            {'name': 'Senior Software Developer', 'dept_code': 'TECH', 'desc': 'Architecture & senior dev responsibilities.'},
            {'name': 'Engineering Lead', 'dept_code': 'TECH', 'desc': 'Manages software development team.'},
            {'name': 'HR Executive', 'dept_code': 'HR', 'desc': 'Handles onboarding and leave operations.'},
            {'name': 'HR Manager', 'dept_code': 'HR', 'desc': 'Head of HR operations.'},
            {'name': 'Senior Accountant', 'dept_code': 'FIN', 'desc': 'Payroll processing and ledger management.'},
            {'name': 'Finance Lead', 'dept_code': 'FIN', 'desc': 'Manages finance operations.'},
        ]

        created_desig = {}
        for des in desig_data:
            dept = created_depts.get(des['dept_code'])
            desig, _ = Designation.objects.get_or_create(
                name=des['name'],
                department=dept,
                defaults={'description': des['desc']}
            )
            created_desig[des['name']] = desig

        # 4. Seed Employee Profiles & Manager Hierarchy
        employees_info = [
            {'email': 'manager1@eelms.com', 'dept_code': 'TECH', 'desig': 'Engineering Lead', 'manager_email': None},
            {'email': 'manager2@eelms.com', 'dept_code': 'FIN', 'desig': 'Finance Lead', 'manager_email': None},
            {'email': 'hr@eelms.com', 'dept_code': 'HR', 'desig': 'HR Manager', 'manager_email': None},
            {'email': 'admin@eelms.com', 'dept_code': 'HR', 'desig': 'HR Executive', 'manager_email': None},
            {'email': 'employee1@eelms.com', 'dept_code': 'TECH', 'desig': 'Software Developer', 'manager_email': 'manager1@eelms.com'},
            {'email': 'employee2@eelms.com', 'dept_code': 'FIN', 'desig': 'Senior Accountant', 'manager_email': 'manager2@eelms.com'},
        ]

        created_employees = {}
        for emp_data in employees_info:
            u = created_users[emp_data['email']]
            dept = created_depts[emp_data['dept_code']]
            desig = created_desig.get(emp_data['desig'])
            
            emp, _ = Employee.objects.get_or_create(
                user=u,
                defaults={
                    'first_name': u.first_name,
                    'last_name': u.last_name,
                    'email': u.email,
                    'department': dept,
                    'designation': desig,
                    'employment_type': EmploymentType.FULL_TIME,
                    'employment_status': EmploymentStatus.ACTIVE,
                }
            )
            created_employees[u.email] = emp

        for emp_data in employees_info:
            if emp_data['manager_email']:
                emp = created_employees[emp_data['email']]
                mgr = created_employees[emp_data['manager_email']]
                emp.manager = mgr
                emp.save()

        self.stdout.write(self.style.SUCCESS(f"Employee Profiles seeded: {len(created_employees)}"))

        # 5. Seed Leave Types & Policies
        leave_types_data = [
            {'code': 'CASUAL', 'name': 'Casual Leave', 'is_paid': True, 'days': 12, 'doc': False},
            {'code': 'SICK', 'name': 'Sick Leave', 'is_paid': True, 'days': 10, 'doc': True},
            {'code': 'EARNED', 'name': 'Earned / Privilege Leave', 'is_paid': True, 'days': 15, 'doc': False},
            {'code': 'MATERNITY', 'name': 'Maternity Leave', 'is_paid': True, 'days': 90, 'doc': True},
            {'code': 'UNPAID', 'name': 'Leave Without Pay (LWP)', 'is_paid': False, 'days': 30, 'doc': False},
        ]

        created_leave_types = {}
        for lt_info in leave_types_data:
            lt, _ = LeaveType.objects.get_or_create(
                code=lt_info['code'],
                defaults={
                    'name': lt_info['name'],
                    'is_paid': lt_info['is_paid'],
                    'max_days_per_year': lt_info['days'],
                    'requires_document': lt_info['doc'],
                    'status': True
                }
            )
            created_leave_types[lt_info['code']] = lt

            LeavePolicy.objects.get_or_create(
                leave_type=lt,
                employment_type=EmploymentType.FULL_TIME,
                defaults={'allocated_days': Decimal(str(lt_info['days']))}
            )

        self.stdout.write(self.style.SUCCESS(f"Leave Types & Policies seeded: {len(created_leave_types)}"))

        # 6. Seed Leave Balances for 2026
        current_year = 2026
        for emp in created_employees.values():
            for lt_code, lt_obj in created_leave_types.items():
                if lt_code in ['CASUAL', 'SICK', 'EARNED']:
                    allocated = Decimal(str(lt_obj.max_days_per_year))
                    LeaveBalance.objects.get_or_create(
                        employee=emp,
                        leave_type=lt_obj,
                        year=current_year,
                        defaults={
                            'allocated_days': allocated,
                            'used_days': Decimal('0.0'),
                            'remaining_days': allocated,
                        }
                    )

        self.stdout.write(self.style.SUCCESS("All seed data created successfully!"))
