/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { ChartRenderer } from './chart_renderer/chart_renderer';
import { Card } from "./card/card";

const actionRegistry = registry.category("actions");
const { onWillStart, useState } = owl;

class MedicalCoverageDashboard extends Component {
    async getCoverageData() {
        // Fetch Refund and categorize them by status
        const coverages = await this.orm.searchRead(
            'hr.medical.coverage', 
            [['status', 'in', ['draft', 'submitted', 'hr_approved', 'hr_rejected', 'finance_approved', 'finance_rejected']], ['create_date', '>', this.state.date]], 
            ['status']
        );


        
        const counts = {
            draft: 0,
            submitted: 0,
            hr_approved: 0,
            hr_rejected: 0,
            finance_approved: 0,
            finance_rejected: 0,
        };

        coverages.forEach(coverage => {
            counts[coverage.status]++;
        });

        this.state.coverages = {
            data: {
                labels: ['Draft', 'Submitted', 'HR Approved', 'HR Rejected', 'Finance Approved', 'Finance Rejected'],
                datasets: [{
                    label: 'Coverage Status',
                    data: [counts.draft, counts.submitted, counts.hr_approved, counts.hr_rejected, counts.finance_approved, counts.finance_rejected],
                    backgroundColor: [
                        'rgb(153, 102, 255)',
                        'rgb(54, 162, 235)',
                        'rgb(75, 192, 192)',
                        'rgb(255, 99, 132)',
                        'rgb(153, 102, 255)',
                        'rgb(255, 159, 64)'
                    ],
                    hoverOffset: 4
                }]
            }
        };
    }

    setup() {
        this.state = useState({
            draft: {value: 0},
            submitted: { value: 0 },
            hr_approved: { value: 0 },
            hr_rejected: { value: 0 },
            finance_approved: { value: 0 },
            finance_rejected: { value: 0 },
            period: 90,
        });
        super.setup();
        this.orm = useService('orm');
        this.actionService = useService('action');

        onWillStart(async () => {
            this.getDates();
            await this.getRequestCounts();
            await this.getCoverageData();
        });
    }

    onChangePeriod() {
        this.getDates();
        this.getRequestCounts();
    }

    getDates() {
        this.state.date = moment().subtract(this.state.period, 'days').format('YYYY-MM-DD');
    }

    async getRequestCounts() {
        // Count requests in each status within the selected period
        const draft = await this.orm.searchCount('hr.medical.coverage', [['status', '=', 'draft'], ['create_date', '>', this.state.date]]);
        const submitted = await this.orm.searchCount('hr.medical.coverage', [['status', '=', 'submitted'], ['create_date', '>', this.state.date]]);
        const hr_approved = await this.orm.searchCount('hr.medical.coverage', [['status', '=', 'hr_approved'], ['create_date', '>', this.state.date]]);
        const hr_rejected = await this.orm.searchCount('hr.medical.coverage', [['status', '=', 'hr_rejected'], ['create_date', '>', this.state.date]]);
        const finance_approved = await this.orm.searchCount('hr.medical.coverage', [['status', '=', 'finance_approved'], ['create_date', '>', this.state.date]]);
        const finance_rejected = await this.orm.searchCount('hr.medical.coverage', [['status', '=', 'finance_rejected'], ['create_date', '>', this.state.date]]);

        this.state.draft.value = draft;
        this.state.submitted.value = submitted;
        this.state.hr_approved.value = hr_approved;
        this.state.hr_rejected.value = hr_rejected;
        this.state.finance_approved.value = finance_approved;
        this.state.finance_rejected.value = finance_rejected;
        // console.log("this is test console" , this.state.hr_approved.value)
    }

    viewRequests(status) {
        // Open action with domain filtered by the status
        const domain = [['status', '=', status]];
        if (this.state.period > 0) {
            domain.push(['create_date', '>', this.state.date]);
        }
        this.actionService.doAction("hr_medical_coverage.hr_medical_coverage_action", {
            additionalContext: {
                type: "ir.actions.act_window",
                name: "Refund",
                res_model: "hr.medical.coverage",
                domain: domain,
                views: [[false, 'list'], [false, 'form']],
            }
        });
    }
}

MedicalCoverageDashboard.template = "hr_medical_coverage.Dashboard";
MedicalCoverageDashboard.components = { ChartRenderer, Card };
actionRegistry.add("hr_medical_coverage.dashboard", MedicalCoverageDashboard);
