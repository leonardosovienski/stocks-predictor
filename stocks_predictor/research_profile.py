"""Personal scenario completeness; missing costs are never silently zero."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ResearchProfile:
    capital_brl: Decimal
    horizon_months: int | None = None
    resident_pf_brazil: bool | None = None
    brokerage_per_order_brl: Decimal | None = None
    monthly_fixed_brl: Decimal | None = None
    advisor_annual_fraction: Decimal | None = None
    loss_limit_brl: Decimal | None = None
    setup_cost_brl: Decimal | None = None
    monthly_maintenance_hours: Decimal | None = None
    hourly_opportunity_cost_brl: Decimal | None = None

    def validate(self) -> None:
        if not self.capital_brl.is_finite() or self.capital_brl <= 0:
            raise ValueError('positive finite capital required')
        if self.horizon_months is not None and (type(self.horizon_months) is not int or self.horizon_months <= 0):
            raise ValueError('positive integer horizon required')
        if self.resident_pf_brazil is not None and type(self.resident_pf_brazil) is not bool:
            raise ValueError('residency must be explicitly confirmed or unknown')
        for value in (self.brokerage_per_order_brl, self.monthly_fixed_brl,
                      self.advisor_annual_fraction, self.loss_limit_brl, self.setup_cost_brl,
                      self.monthly_maintenance_hours, self.hourly_opportunity_cost_brl):
            if value is not None and (not value.is_finite() or value < 0):
                raise ValueError('costs and loss limits must be finite and nonnegative')
        if self.advisor_annual_fraction is not None and self.advisor_annual_fraction > 1:
            raise ValueError('advisor rate must be a fraction between zero and one')

    def assess(self, *, planned_orders: int = 2) -> dict:
        self.validate()
        if type(planned_orders) is not int or planned_orders < 0:
            raise ValueError('planned_orders must be a nonnegative integer')
        required = ('horizon_months', 'resident_pf_brazil', 'brokerage_per_order_brl',
                    'monthly_fixed_brl', 'advisor_annual_fraction', 'setup_cost_brl',
                    'monthly_maintenance_hours', 'hourly_opportunity_cost_brl')
        missing = [key for key in required if getattr(self, key) is None]
        fixed = None
        if self.horizon_months is not None and self.monthly_fixed_brl is not None and self.brokerage_per_order_brl is not None:
            fixed = self.monthly_fixed_brl * self.horizon_months + self.brokerage_per_order_brl * planned_orders
        project_cost = None
        if (self.horizon_months is not None and self.setup_cost_brl is not None
                and self.monthly_maintenance_hours is not None and self.hourly_opportunity_cost_brl is not None):
            project_cost = self.setup_cost_brl + self.horizon_months * self.monthly_maintenance_hours * self.hourly_opportunity_cost_brl
        return {
            'status': 'INCOMPLETE_PERSONAL_SCENARIO' if missing else 'INPUTS_COMPLETE_NOT_PROFIT_VALIDATION',
            'capital_brl': str(self.capital_brl), 'missing_inputs': missing,
            'planned_orders': planned_orders,
            'known_fixed_reserve_brl': None if fixed is None else str(fixed),
            'fixed_reserve_fits_capital': None if fixed is None else fixed < self.capital_brl,
            'project_and_time_cost_brl': None if project_cost is None else str(project_cost),
            'cost_scope': 'Brokerage/fixed reserve and project opportunity cost are separate; taxes and exchange fees still require applicable trade records.',
            'advisor_cost_basis': 'requires future valuation path; rate is not a fixed expense',
            'risk_limit_confirmed': self.loss_limit_brl is not None,
            'absolute_net_profit_demonstrated': False, 'capital_enabled': False,
        }
