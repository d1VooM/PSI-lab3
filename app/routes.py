from flask import Blueprint, current_app, jsonify, render_template, request

from .converter import convert, quantize
from .errors import SourceUnavailable, ValidationError
from .validation import parse_amount

bp = Blueprint("main", __name__)


def _meta(payload):
    return {k: v for k, v in payload.items() if k != "rates"}


@bp.get("/")
def index():
    return render_template("index.html")


@bp.get("/api/rates")
def rates():
    p = current_app.extensions["rates"].get_rates()
    order = {"MDL": 0, "EUR": 1, "USD": 2}
    items = [{"code": c, "name": r["name"], "nominal": r["nominal"], "value": r["value"]}
             for c, r in p["rates"].items()]
    items.sort(key=lambda x: (order.get(x["code"], 9), x["code"]))
    return jsonify({**_meta(p), "currencies": items})


@bp.post("/api/convert")
def do_convert():
    body = request.get_json(silent=True) or {}
    amount = parse_amount(body.get("amount"))
    src = str(body.get("from") or "").upper()
    dst = str(body.get("to") or "").upper()
    p = current_app.extensions["rates"].get_rates()
    result, rate = convert(amount, src, dst, p["rates"])
    return jsonify({
        **_meta(p), "amount": str(amount), "from": src, "to": dst,
        "result": str(quantize(result, 4)), "rate": str(quantize(rate, 6)),
        "same_currency": src == dst,
    })


@bp.get("/api/neo")
def neo():
    return jsonify(current_app.extensions["neo"].get(request.args.get("date")))


@bp.app_errorhandler(ValidationError)
def _bad_input(exc):
    return jsonify({"error": str(exc)}), 400


@bp.app_errorhandler(SourceUnavailable)
def _unavailable(exc):
    return jsonify({"error": str(exc)}), 503
