from ..models import TariffPlan

CURRENCY = "руб."


def format_tariff_plan(plan: TariffPlan) -> str:
    return f"""\n• <b>{plan.name}</b> - {plan.price} {CURRENCY} - цели: {plan.targets_limit}
{plan.description}\n"""
