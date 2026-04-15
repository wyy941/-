from flask import request
from flask_restful import Resource

from services.cache_service import cache_delete_prefix
from services.sample_data_service import import_sample_data, preview_sample_data
from utils.permissions import require_admin
from utils.response import error, success


class SampleDataPreviewResource(Resource):
    def get(self):
        _, response = require_admin()
        if response is not None:
            return response

        limit = request.args.get("limit", default=10, type=int) or 10

        try:
            return success(preview_sample_data(limit))
        except FileNotFoundError as exc:
            return error(str(exc), 404)


class SampleDataImportResource(Resource):
    def post(self):
        _, response = require_admin()
        if response is not None:
            return response

        data = request.get_json(silent=True) or {}
        limit = data.get("limit")

        try:
            result = import_sample_data(limit=int(limit) if limit else None)
        except FileNotFoundError as exc:
            return error(str(exc), 404)
        except ValueError:
            return error("limit 必须为整数")

        cache_delete_prefix("dashboard:overview:")
        return success(result, "示例数据导入完成", 201)
