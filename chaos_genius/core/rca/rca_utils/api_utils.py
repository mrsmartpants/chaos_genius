"""Utility functions for RCA API endpoints."""
import logging
from datetime import date, datetime, timedelta
from typing import List
from chaos_genius.databases.models.anomaly_data_model import AnomalyDataOutput

from chaos_genius.extensions import db
from chaos_genius.controllers.kpi_controller import get_kpi_data_from_id
from chaos_genius.core.rca.constants import TIME_RANGES_BY_KEY
from chaos_genius.databases.models.rca_data_model import RcaData
from chaos_genius.utils.datetime_helper import (
    convert_datetime_to_timestamp,
    get_datetime_string_with_tz,
    get_lastscan_string_with_tz,
    get_rca_date_from_string,
)
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)


def kpi_aggregation(kpi_id, timeline="last_30_days"):
    """Get KPI aggregation data."""
    final_data = {}
    status = "success"
    message = ""
    try:
        kpi_info = get_kpi_data_from_id(kpi_id)
        end_date = get_rca_output_end_date(kpi_info)

        data_point = (
            RcaData.query.filter(
                (RcaData.kpi_id == kpi_id)
                & (RcaData.data_type == "agg")
                & (RcaData.timeline == timeline)
                & (RcaData.end_date <= end_date)
            )
            .order_by(RcaData.created_at.desc())
            .first()
        )

        rca_end_date = data_point.end_date

        anomaly_data_point = AnomalyDataOutput.query.filter(
            (AnomalyDataOutput.kpi_id == kpi_id)
            & (AnomalyDataOutput.anomaly_type == "overall")
            & (AnomalyDataOutput.is_anomaly != 0)
            & (AnomalyDataOutput.data_datetime <= rca_end_date + timedelta(days=1))
            & (AnomalyDataOutput.data_datetime >= rca_end_date - timedelta(days=7))
        ).count()

        if data_point:
            analysis_date = get_analysis_date(kpi_id, end_date)
            final_data = {
                "aggregation": [
                    {
                        "label": "group1_value",
                        "value": data_point.data["group1_value"],
                    },
                    {
                        "label": "group2_value",
                        "value": data_point.data["group2_value"],
                    },
                    {
                        "label": "difference",
                        "value": data_point.data["difference"],
                    },
                    {
                        "label": "perc_change",
                        "value": data_point.data["perc_change"],
                    },
                    {
                        "label": "anomalous_points",
                        "value": anomaly_data_point,
                    },
                ],
                "analysis_date": get_datetime_string_with_tz(analysis_date),
                "timecuts_date": get_timecuts_dates(analysis_date, timeline),
                "last_run_time_rca": get_lastscan_string_with_tz(
                    kpi_info["scheduler_params"]["last_scheduled_time_rca"]
                ),
                "anomalous_points_str": "Last 7 Days",
            }
        else:
            raise ValueError("No data found")
    except Exception as err:  # noqa: B902
        logger.error(f"Error in KPI aggregation retrieval: {err}", exc_info=1)
        status = "error"
        message = str(err)
        final_data = {
            "aggregation": [
                {
                    "label": "group1_value",
                    "value": "-",
                },
                {
                    "label": "group2_value",
                    "value": "-",
                },
                {
                    "label": "difference",
                    "value": "-",
                },
                {
                    "label": "perc_change",
                    "value": "-",
                },
            ],
            "analysis_date": "",
        }
    return status, message, final_data


def kpi_line_data(kpi_id, download=False):
    """Get KPI line data."""
    final_data = []
    status = "success"
    message = ""
    try:
        kpi_info = get_kpi_data_from_id(kpi_id)
        end_date = get_rca_output_end_date(kpi_info)

        data_point = (
            RcaData.query.filter(
                (RcaData.kpi_id == kpi_id)
                & (RcaData.data_type == "line")
                & (RcaData.end_date <= end_date)
            )
            .order_by(RcaData.created_at.desc())
            .first()
        )

        if not data_point:
            raise ValueError("No data found.")

        final_data = data_point.data
        if not download:
            for row in final_data:
                row["date"] = convert_datetime_to_timestamp(
                    get_rca_date_from_string(row["date"])
                )
        else:
            for row in final_data:
                row["date"] = get_rca_date_from_string(row["date"])

    except Exception as err:  # noqa: B902
        logger.error(f"Error in KPI Line data retrieval: {err}", exc_info=1)
        status = "error"
        message = str(err)
    return status, message, final_data


def rca_analysis(kpi_id, timeline="last_30_days", dimension=None):
    """Get RCA analysis data."""
    final_data = {}
    status = "success"
    message = ""
    try:
        kpi_info = get_kpi_data_from_id(kpi_id)
        end_date = get_rca_output_end_date(kpi_info)

        data_point = (
            RcaData.query.filter(
                (RcaData.kpi_id == kpi_id)
                & (RcaData.data_type == "rca")
                & (RcaData.timeline == timeline)
                & (RcaData.end_date <= end_date)
                & (RcaData.dimension == dimension)
            )
            .order_by(RcaData.created_at.desc())
            .first()
        )

        if data_point:
            final_data = data_point.data
            final_data["analysis_date"] = get_datetime_string_with_tz(
                get_analysis_date(kpi_id, end_date)
            )
        else:
            raise ValueError("No data found.")
    except Exception as err:  # noqa: B902
        logger.error(f"Error in RCA Analysis retrieval: {err}", exc_info=1)
        status = "error"
        message = str(err)
        final_data = {
            "chart": {
                "chart_data": [],
                "y_axis_lim": [],
                "chart_table": [],
            },
            "data_table": [],
            "analysis_date": "",
        }
    return status, message, final_data


def rca_hierarchical_data(kpi_id, timeline="last_30_days", dimension=None):
    """Get RCA hierarchical data."""
    final_data = {}
    status = "success"
    message = ""
    try:
        kpi_info = get_kpi_data_from_id(kpi_id)
        end_date = get_rca_output_end_date(kpi_info)

        data_point = (
            RcaData.query.filter(
                (RcaData.kpi_id == kpi_id)
                & (RcaData.data_type == "htable")
                & (RcaData.timeline == timeline)
                & (RcaData.end_date <= end_date)
                & (RcaData.dimension == dimension)
            )
            .order_by(RcaData.created_at.desc())
            .first()
        )

        if data_point:
            final_data = data_point.data
            final_data["analysis_date"] = get_datetime_string_with_tz(
                get_analysis_date(kpi_id, end_date)
            )
        else:
            raise ValueError("No data found.")
    except Exception as err:  # noqa: B902
        logger.error(
            f"Error in RCA hierarchical table retrieval: {err}", exc_info=1
        )
        status = "error"
        message = str(err)
        final_data = {"data_table": [], "analysis_date": ""}
    return status, message, final_data


def rca_hierarchical_data_all_dims(kpi_id, timeline="last_30_days"):
    """Get RCA hierarchical data for all dimensions."""
    final_data_list = {}
    status = "success"
    message = ""
    try:
        kpi_info = get_kpi_data_from_id(kpi_id)
        end_date = get_rca_output_end_date(kpi_info)

        subq = (
            db.session.query(
                RcaData.dimension,
                func.max(RcaData.created_at).label("latest_created_at"),
            )
            .filter(RcaData.kpi_id == kpi_id)
            .group_by(RcaData.dimension)
            .subquery()
        )

        data_points = (
            db.session.query(RcaData)
            .filter(
                (RcaData.kpi_id == kpi_id)
                & (RcaData.data_type == "htable")
                & (RcaData.timeline == timeline)
                & (RcaData.end_date <= end_date)
            )
            .join(
                subq,
                and_(
                    RcaData.dimension == subq.c.dimension,
                    RcaData.created_at == subq.c.latest_created_at,
                ),
            )
            .all()
        )

        final_data_list = []
        if data_points:
            for data_point in data_points:
                final_data = data_point.data
                final_data["analysis_date"] = get_datetime_string_with_tz(
                    get_analysis_date(kpi_id, end_date)
                )
                final_data["dimension"] = data_point.dimension
                final_data_list.append(final_data)
        else:
            raise ValueError("No data found.")
    except Exception as err:  # noqa: B902
        logger.error(f"Error in RCA hierarchical table retrieval: {err}", exc_info=1)
        status = "error"
        message = str(err)
        final_data_list = []
    return status, message, final_data_list


def get_rca_output_end_date(kpi_info: dict) -> date:
    """Get RCA end date."""
    end_date = None

    if kpi_info["is_static"]:
        end_date = kpi_info["static_params"].get("end_date")

    if end_date is None:
        return datetime.today().date()
    else:
        return datetime.strptime(end_date, "%Y-%m-%d").date()


def get_analysis_date(kpi_id: int, end_date: date) -> date:
    """Get analysis date for RCA."""
    data_point = (
        RcaData.query.filter(
            (RcaData.kpi_id == kpi_id)
            & (RcaData.data_type == "line")
            & (RcaData.end_date <= end_date)
        )
        .order_by(RcaData.created_at.desc())
        .first()
    )
    final_data = data_point.data if data_point else []
    analysis_date = final_data[-1]["date"]
    return get_rca_date_from_string(analysis_date)


def get_timecuts_dates(analysis_date: date, timeline: str) -> List:
    """Get timecuts dates for RCA."""
    (g1_sd, g1_ed), (g2_sd, g2_ed) = TIME_RANGES_BY_KEY[timeline]["function"](
        analysis_date
    )

    output = [
        {
            "label": "group1_value",
            "start_date": g1_sd,
            "end_date": g1_ed,
        },
        {
            "label": "group2_value",
            "start_date": g2_sd,
            "end_date": g2_ed,
        },
    ]

    if timeline == "previous_day":
        del output[0]["start_date"]
        del output[1]["start_date"]

    return output
