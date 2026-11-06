from typing import Any

from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from acl.models import ACLBase
from airone.celery import app
from airone.lib.job import may_schedule_until_job_is_ready, register_job_task
from airone.lib.log import Logger
from group.models import Group
from job.models import Job, JobOperation, JobStatus
from job.params import RoleChangeParams, RoleImportParams, RoleReferralParams
from role.history import suppress_role_history
from role.models import Role
from role.services import restore_data, validate_role_data
from user.models import User


@register_job_task(JobOperation.ROLE_REGISTER_REFERRAL)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def edit_role_referrals(self: Any, job: Job) -> JobStatus:
    params = job.get_typed_params(RoleReferralParams)
    role = Role.objects.get(id=params.role_id)

    for entry in [x for x in role.get_referred_entries()]:
        entry.register_es()

    return JobStatus.DONE


@register_job_task(JobOperation.IMPORT_ROLE_V2)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def import_role_v2(self: Any, job: Job) -> tuple[JobStatus, str, None] | None:
    import_data = job.get_typed_params(RoleImportParams).root
    err_msg = []
    total_count = len(import_data)

    for index, role_data in enumerate(import_data):
        job.text = "Now importing roles... (progress: [%5d/%5d])" % (index + 1, total_count)
        job.save(update_fields=["text"])

        duplicate_users = sorted(set(role_data.users) & set(role_data.admin_users))
        duplicate_groups = sorted(set(role_data.groups) & set(role_data.admin_groups))
        if duplicate_users or duplicate_groups:
            details = []
            if duplicate_users:
                details.append("users: " + ", ".join(duplicate_users))
            if duplicate_groups:
                details.append("groups: " + ", ".join(duplicate_groups))
            err_msg.append(
                "role '%s' has the same member and administrator: %s"
                % (role_data.name, "; ".join(details))
            )
            continue

        # Interrupt processing if the job is canceled
        if job.is_canceled():
            job.status = JobStatus.CANCELED
            job.save(update_fields=["status"])
            return None

        # Retrieve or create roles
        if role_data.id is not None:
            role = Role.objects.filter(id=role_data.id).first()
            if not role:
                err_msg.append(f"Role with ID {role_data.id} does not exist.")
                continue

            if (role.name != role_data.name) and (
                Role.objects.filter(name=role_data.name).count() > 0
            ):
                err_msg.append(
                    "New role name is already used(id:%s, group:%s->%s)"
                    % (role_data.id, role.name, role_data.name)
                )
                continue

            role._history_user = job.user
            role._change_reason = f"Job #{job.pk}; import"
            if not role.history.exists():
                role.save()
            role.name = role_data.name
        else:
            # Update the group by name
            role = Role.objects.filter(name=role_data.name).first()
            if not role:
                # create group
                role = Role(name=role_data.name)
                role._history_user = job.user
                role._change_reason = f"Job #{job.pk}; import"
                role.save()
            else:
                role._history_user = job.user
                role._change_reason = f"Job #{job.pk}; import"
                # Clear registered members (users, groups, and administrative ones) for that role
                for key in ["users", "groups", "admin_users", "admin_groups"]:
                    getattr(role, key).clear()

        # Update role information
        role.description = role_data.description

        # Configure associated users and groups
        for key in ["users", "admin_users"]:
            for name in getattr(role_data, key):
                instance = User.objects.filter(username=name, is_active=True).first()
                if not instance:
                    err_msg.append("specified user is not found (username: %s)" % name)
                    continue
                getattr(role, key).add(instance)

        for key in ["groups", "admin_groups"]:
            for name in getattr(role_data, key):
                group_instance = Group.objects.filter(
                    name=name,
                    is_active=True,
                ).first()
                if not group_instance:
                    err_msg.append("specified group is not found (name: %s)" % name)
                    continue
                getattr(role, key).add(group_instance)

        # Configure ACL
        for permission in role_data.permissions:
            acl = ACLBase.objects.filter(id=permission["obj_id"]).first()
            if not acl:
                raise ValueError(f"Invalid obj_id: {permission['obj_id']}")
            if permission["permission"] in ("readable", "writable", "full"):
                permission_obj = getattr(acl, permission["permission"])
                permission_obj._history_user = job.user
                permission_obj._change_reason = f"Job #{job.pk}; import"
                permission_obj.roles.add(role)

        try:
            role.save()
        except Exception as e:
            err_msg.append(role_data.name)
            Logger.warning("failed to save role: name=%s, error=%s" % (role_data.name, str(e)))

    # Update the job based on the result of the process
    if err_msg:
        return (
            JobStatus.WARNING,
            "Imported Role count: %d, Failed import Roles: %s"
            % (total_count - len(err_msg), err_msg),
            None,
        )
    else:
        return JobStatus.DONE, "Imported Role count: %d" % total_count, None


@register_job_task(JobOperation.EDIT_ROLE)
@register_job_task(JobOperation.DELETE_ROLE)
@register_job_task(JobOperation.RESTORE_ROLE)
@app.task(bind=True)
@may_schedule_until_job_is_ready
def change_role(self: Any, job: Job) -> JobStatus:
    params = job.get_typed_params(RoleChangeParams)
    with transaction.atomic():
        roles = Role.objects.select_for_update()
        if job.operation != JobOperation.RESTORE_ROLE:
            roles = roles.filter(is_active=True)
        role = roles.get(pk=params.role_id)
        user = User.objects.get(pk=job.user_id)
        if not user.is_active or user.is_readonly or not role.is_editable(user):
            raise PermissionDenied("You do not have permission to change this role")
        role._history_user = user
        role._change_reason = f"Job #{job.pk}"
        if not role.history.exists():
            role.save()
        old_name = role.name
        if job.operation == JobOperation.DELETE_ROLE:
            role.delete()
            return JobStatus.DONE
        data = params.data
        permission_ids = None
        if job.operation == JobOperation.RESTORE_ROLE:
            if params.history_id is None:
                raise ValueError("history_id is required")
            data, permission_ids = restore_data(role, params.history_id, user)
            role._change_reason += f"; restored history #{params.history_id}"
        serializer = validate_role_data(role, data, user)
        token = suppress_role_history.set(True)
        role.skip_history_when_saving = True
        try:
            serializer.save()
            if permission_ids is not None:
                role.permissions.set(permission_ids)
        finally:
            del role.skip_history_when_saving
            suppress_role_history.reset(token)
        role.save()
        if old_name != role.name:
            referral_job = Job.new_register_referrals(
                user,
                None,
                operation_value=JobOperation.ROLE_REGISTER_REFERRAL,
                params={"role_id": role.pk},
            )
            transaction.on_commit(referral_job.run)
    return JobStatus.DONE
