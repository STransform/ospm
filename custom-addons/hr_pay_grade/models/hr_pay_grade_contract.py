from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    pay_grade_id = fields.Many2one(
        "hr.pay.grade",
        compute="_compute_pay_grade",
        string="Pay Grade",
        readonly=True,
        store=True,
        help="Pay grade for the contract.",
    )
    increment_level_id = fields.Many2one(
        "hr.pay.grade.increment",
        string="Increment Level",
        domain="[('pay_grade_id', '=', pay_grade_id)]",
        help="Select the increment level within the pay grade.",
    )
    is_base = fields.Boolean(
        string="Base Salary", help="Indicates selection of Base salary."
    )
    is_ceiling = fields.Boolean(
        string="Ceiling Salary", help="Indicates selection of Ceiling salary."
    )
    is_base_or_ceil = fields.Boolean(string="Base or Ceil")
    wage = fields.Float(
        string="Wage",
        compute="_compute_wage",
        store=True,
        readonly=True,
        help="Salary based on pay grade and increment level.",
    )

    @api.depends("job_id")
    def _compute_pay_grade(self):
        for record in self:
            pay_grade = self.env["hr.pay.grade"].search(
                [("job_ids", "in", record.job_id.id)], limit=1
            )
            record.pay_grade_id = pay_grade

    @api.depends("is_base", "is_ceiling", "increment_level_id", "pay_grade_id")
    def _compute_wage(self):
        """Compute wage based on base, ceiling, or increment selection."""
        for record in self:
            if record.is_base:
                record.wage = record.pay_grade_id.base_salary
            elif record.is_ceiling:
                record.wage = record.pay_grade_id.ceiling_salary
            elif record.increment_level_id:
                record.wage = record.increment_level_id.salary
            else:
                record.wage = 0.0

    @api.onchange("is_base", "is_ceiling")
    def _is_base_or_ceil(self):
        for record in self:
            if record.is_base or record.is_ceiling:
                record.is_base_or_ceil = True
            else:
                record.is_base_or_ceil = False

    @api.onchange("is_ceiling")
    def _onchange_base(self):
        """Automatically deselect the other option."""
        for record in self:
            if record.is_ceiling:
                record.is_base = False  # Deselect Base if Ceiling is selected
                record.increment_level_id = False  # Clear increment level

    @api.onchange("is_base")
    def _onchange_ceiling(self):
        for record in self:
            if record.is_base:
                record.is_ceiling = False  # Deselect Ceiling if Base is selected
                record.increment_level_id = False  # Clear increment level
