import csv
import io
import json

import yaml
from django.conf import settings
from natsort import natsorted

from airone.celery import app
from airone.lib.types import AttrTypeValue
from entry.models import Entry
from job.models import Job


def _csv_export(job, values, recv_data, has_referral):
    output = io.StringIO(newline="")
    writer = csv.writer(output)

    # write first line of CSV
    if has_referral is not False:
        writer.writerow(
            ["Name"] + ["Entity"] + [x["name"] for x in recv_data["attrinfo"]] + ["Referral"]
        )
    else:
        writer.writerow(["Name"] + ["Entity"] + [x["name"] for x in recv_data["attrinfo"]])

    for (index, entry_info) in enumerate(values):
        line_data = [entry_info["entry"]["name"]]

        # Abort processing when job is canceled
        if index % Job.STATUS_CHECK_FREQUENCY == 0 and job.is_canceled():
            return

        # Append the data which specifies Entity name to which target Entry belongs
        line_data.append(entry_info["entity"]["name"])

        for attrinfo in recv_data["attrinfo"]:
            # This condition eliminates the possibility that an attribute
            # which target entry doens't have is specified in attrinfo variable.
            if attrinfo["name"] not in entry_info["attrs"]:
                line_data.append("")
                continue

            value = entry_info["attrs"][attrinfo["name"]]

            vtype = None
            if (value is not None) and ("type" in value):
                vtype = value["type"]

            vval = None
            if (value is not None) and ("value" in value):
                vval = value["value"]

            if not value or "value" not in value or not value["value"]:
                line_data.append("")

            elif (
                vtype == AttrTypeValue["string"]
                or vtype == AttrTypeValue["text"]
                or vtype == AttrTypeValue["boolean"]
                or vtype == AttrTypeValue["date"]
            ):

                line_data.append(str(vval))

            elif vtype == AttrTypeValue["object"] or vtype == AttrTypeValue["group"]:

                line_data.append(str(vval["name"]))

            elif vtype == AttrTypeValue["named_object"]:

                [(k, v)] = vval.items()
                line_data.append("%s: %s" % (k, v["name"]))

            elif vtype == AttrTypeValue["array_string"]:

                line_data.append("\n".join(natsorted(vval)))

            elif vtype == AttrTypeValue["array_object"] or vtype == AttrTypeValue["array_group"]:

                line_data.append("\n".join(natsorted([x["name"] for x in vval])))

            elif vtype == AttrTypeValue["array_named_object"]:

                items = []
                for vset in vval:
                    [(k, v)] = vset.items()
                    items.append("%s: %s" % (k, v["name"]))

                line_data.append("\n".join(natsorted(items)))

        if has_referral is not False:
            line_data.append(
                str(["%s / %s" % (x["name"], x["schema"]["name"]) for x in entry_info["referrals"]])
            )

        writer.writerow(line_data)

    return output


def _yaml_export(job, values, recv_data, has_referral):
    output = io.StringIO()

    def _get_attr_value(atype, value):
        if atype & AttrTypeValue["array"]:
            return [_get_attr_value(atype ^ AttrTypeValue["array"], x) for x in value]

        if atype == AttrTypeValue["named_object"]:
            [(key, val)] = value.items()

            return {key: val["name"]}

        elif atype == AttrTypeValue["object"] or atype == AttrTypeValue["group"]:
            return value["name"]

        elif atype == AttrTypeValue["boolean"]:
            return True if value == "True" else False

        else:
            return value

    resp_data = {}
    for (index, entry_info) in enumerate(values):
        data = {
            "name": entry_info["entry"]["name"],
            "attrs": {},
        }

        # Abort processing when job is canceled
        if index % Job.STATUS_CHECK_FREQUENCY == 0 and job.is_canceled():
            return

        for attrinfo in recv_data["attrinfo"]:
            if attrinfo["name"] in entry_info["attrs"]:
                _adata = entry_info["attrs"][attrinfo["name"]]
                if "value" not in _adata:
                    continue

                data["attrs"][attrinfo["name"]] = _get_attr_value(_adata["type"], _adata["value"])

        if has_referral is not False:
            data["referrals"] = [
                {
                    "entity": x["schema"]["name"],
                    "entry": x["name"],
                }
                for x in entry_info["referrals"]
            ]

        if entry_info["entity"]["name"] in resp_data:
            resp_data[entry_info["entity"]["name"]].append(data)
        else:
            resp_data[entry_info["entity"]["name"]] = [data]

    output.write(yaml.dump(resp_data, default_flow_style=False, allow_unicode=True))

    return output


@app.task(bind=True)
def export_search_result(self, job_id):
    job = Job.objects.get(id=job_id)

    if not job.proceed_if_ready():
        return

    # set flag to indicate that this job starts processing
    job.update(Job.STATUS["PROCESSING"])

    user = job.user
    recv_data = json.loads(job.params)

    # Do not care whether the "has_referral" value is
    has_referral = recv_data.get("has_referral", False)
    referral_name = recv_data.get("referral_name")
    entry_name = recv_data.get("entry_name")

    if has_referral and referral_name is None:
        referral_name = ""

    resp = Entry.search_entries(
        user,
        recv_data["entities"],
        recv_data["attrinfo"],
        settings.ES_CONFIG["MAXIMUM_RESULTS_NUM"],
        entry_name,
        referral_name,
    )

    io_stream = None
    if recv_data["export_style"] == "yaml":
        io_stream = _yaml_export(job, resp["ret_values"], recv_data, has_referral)

    elif recv_data["export_style"] == "csv":
        io_stream = _csv_export(job, resp["ret_values"], recv_data, has_referral)

    if io_stream:
        job.set_cache(io_stream.getvalue())

    # update job status and save it except for the case that target job is canceled.
    if not job.is_canceled():
        job.update(Job.STATUS["DONE"])
