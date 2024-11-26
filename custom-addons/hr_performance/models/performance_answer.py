from odoo import models, fields

class HrPerformanceMeasureAnswer(models.Model):
    _name = 'hr.performance.evaluation.answer'
    _description = 'Performance Evaluation Question and Answer'

    performance_evaluation_id = fields.Many2one('hr.performance.evaluation', string="Performance Measure", ondelete="cascade")
    question = fields.Char("Rating Factor", required=True)
    answer = fields.Char("Rating", required=True)
    score = fields.Float("Score", required=False)  # Optional, if you want to track scores for each answer
