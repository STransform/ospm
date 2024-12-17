/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onWillStart, useState } from "@odoo/owl";
import { Chart } from 'chart.js'; // Ensure Chart.js is installed and available

const actionRegistry = registry.category("actions");

class HrSalaryIncrementEmployeeDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        
        this.chartByApprover = null; // Chart instance for increments by approver
        this.chartByMonth = null;    // Chart instance for increments by month

        this.state = useState({
            incrementHistory: [],
            period: 90,
            date: null,
        });

        onWillStart(async () => {
            this.computeDate();
            await this.loadIncrementHistory();
        });

        onMounted(() => {
            this.updateCharts();
        });
    }

    computeDate() {
        // Using moment.js here if already present, otherwise adjust:
        this.state.date = moment().subtract(this.state.period, "days").format("YYYY-MM-DD");
    }

    async loadIncrementHistory() {
        const domain = [["increment_date", ">", this.state.date]];
        const fields = ["employee_id", "increment_date", "approved_by", "from_increment_name", "to_increment_name"];
        const history = await this.orm.searchRead("hr.salary.increment.history", domain, fields);

        this.state.incrementHistory = history;
        this.updateCharts();
    }

    updateCharts() {
        this.updateApproverChart();
        this.updateMonthlyChart();
    }

    updateApproverChart() {
        if (this.chartByApprover) {
            this.chartByApprover.destroy();
            this.chartByApprover = null;
        }

        const ctx = this.el.querySelector("#approverChart");
        if (!ctx) return;

        // Count increments by approver
        const incrementsByApprover = {};
        for (const rec of this.state.incrementHistory) {
            const approverName = rec.approved_by ? rec.approved_by[1] : "Unknown";
            incrementsByApprover[approverName] = (incrementsByApprover[approverName] || 0) + 1;
        }

        const approvers = Object.keys(incrementsByApprover);
        const counts = Object.values(incrementsByApprover);

        this.chartByApprover = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: approvers,
                datasets: [{
                    label: 'Increments by Approver',
                    data: counts,
                    backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Increments by Approver'
                    }
                }
            }
        });
    }

    updateMonthlyChart() {
        if (this.chartByMonth) {
            this.chartByMonth.destroy();
            this.chartByMonth = null;
        }

        const ctx = this.el.querySelector("#monthlyChart");
        if (!ctx) return;

        // Count increments by month
        const incrementsByMonth = {};
        for (const rec of this.state.incrementHistory) {
            const date = moment(rec.increment_date);
            const monthLabel = date.format("YYYY-MM"); // year-month format
            incrementsByMonth[monthLabel] = (incrementsByMonth[monthLabel] || 0) + 1;
        }

        const months = Object.keys(incrementsByMonth).sort();
        const counts = months.map(m => incrementsByMonth[m]);

        this.chartByMonth = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [{
                    label: 'Increments per Month',
                    data: counts,
                    backgroundColor: '#4e73df'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Increments Over Time'
                    }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
}

HrSalaryIncrementEmployeeDashboard.template = "hr_salary_increment_employee.Dashboard";
actionRegistry.add("hr_salary_increment.employee_dashboard", HrSalaryIncrementEmployeeDashboard);

export default HrSalaryIncrementEmployeeDashboard;
