from odoo import models, api, fields
from odoo.exceptions import ValidationError


class HrPayGradeIncrement(models.Model):
    _name = "hr.pay.grade.increment"
    _description = "Pay Grade Increment"

    pay_grade_id = fields.Many2one(
        "hr.pay.grade", string="Pay Grade", required=True, ondelete="cascade"
    )
    increment = fields.Selection(
        selection=[(str(i), f"Step {i}") for i in range(1, 10)],
        string="Increment Level",
        required=True,
        help="Select the increment level (1-9) for the pay grade.",
    )
    salary = fields.Float(string="Salary", required=True)

    _sql_constraints = [
        (
            "increment_unique",
            "unique(pay_grade_id, increment)",
            "Each increment level within a pay grade must be unique.",
        ),
    ]

    def name_get(self):
        return [(record.id, f"Increment - {record.increment}") for record in self]

    @api.constrains("salary")
    def _check_salary_within_bounds(self):
        for record in self:
            if not (
                record.pay_grade_id.base_salary
                <= record.salary
                <= record.pay_grade_id.ceiling_salary
            ):
                raise ValidationError(
                    "Salary must be within the base and ceiling salary range of the pay grade."
                )
