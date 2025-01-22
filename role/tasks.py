import json

from acl.models import ACLBase
from airone.celery import app
from airone.lib.job import may_schedule_until_job_is_ready
from airone.lib.log import Logger
from group.models import Group
from job.models import Job, JobStatus
from role.models import Role
from user.models import User


@app.task(bind=True)
@may_schedule_until_job_is_ready
def edit_role_referrals(self, job: Job) -> JobStatus:
    params = json.loads(job.params)
    role = Role.objects.get(id=params["role_id"])

    for entry in [x for x in role.get_referred_entries()]:
        entry.register_es()

    return JobStatus.DONE


@app.task(bind=True)
@may_schedule_until_job_is_ready
def import_role_v2(self, job: Job) -> tuple[JobStatus, str, None] | None:
    job_id = job.id
    job: Job = Job.objects.get(id=job_id)

    import_data = json.loads(job.params)
    err_msg = []

    total_count = len(import_data)

    for index, role_data in enumerate(import_data):
        job.text = "Now importing roles... (progress: [%5d/%5d])" % (index + 1, total_count)
        job.save(update_fields=["text"])

        # Interrupt processing if the job is canceled
        if job.is_canceled():
            job.status = JobStatus.CANCELED
            job.save(update_fields=["status"])
            return

        # Skip processing if the role name is not provided
        if "name" not in role_data:
            err_msg.append("Role name is required")
            continue

        # Retrieve or create roles
        if "id" in role_data:
            role = Role.objects.filter(id=role_data["id"]).first()
            if not role:
                err_msg.append(f"Role with ID {role_data['id']} does not exist.")
                continue

            if (role.name != role_data["name"]) and (
                Role.objects.filter(name=role_data["name"]).count() > 0
            ):
                err_msg.append(
                    "New role name is already used(id:%s, group:%s->%s)"
                    % (role_data["id"], role.name, role_data["name"])
                )
                continue

            role.name = role_data["name"]
        else:
            # Update the group by name
            role = Role.objects.filter(name=role_data["name"]).first()
            if not role:
                # create group
                role = Role.objects.create(name=role_data["name"])
            else:
                # Clear registered members (users, groups, and administrative ones) for that role
                for key in ["users", "groups", "admin_users", "admin_groups"]:
                    getattr(role, key).clear()

        # Update role information
        role.description = role_data.get("description", "")

        # Configure associated users and groups
        for key in ["users", "admin_users"]:
            for name in role_data[key]:
                instance = User.objects.filter(username=name, is_active=True).first()
                if not instance:
                    err_msg.append("specified user is not found (username: %s)" % name)
                    continue
                getattr(role, key).add(instance)

        for key in ["groups", "admin_groups"]:
            for name in role_data[key]:
                instance = Group.objects.filter(name=name, is_active=True).first()
                if not instance:
                    err_msg.append("specified group is not found (name: %s)" % name)
                    continue
                getattr(role, key).add(instance)

        # Configure ACL
        for permission in role_data.get("permissions", []):
            acl = ACLBase.objects.filter(id=permission["obj_id"]).first()
            if not acl:
                raise ValueError(f"Invalid obj_id: {permission['obj_id']}")
            if permission["permission"] == "readable":
                acl.readable.roles.add(role)
            elif permission["permission"] == "writable":
                acl.writable.roles.add(role)
            elif permission["permission"] == "full":
                acl.full.roles.add(role)

        try:
            role.save()
        except Exception as e:
            err_msg.append(role_data["name"])
            Logger.warning("failed to save role: name=%s, error=%s" % (role_data["name"], str(e)))

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
