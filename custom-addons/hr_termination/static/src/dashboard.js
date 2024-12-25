/**@odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from  "@odoo/owl";
import {ChartRenderer} from './chart_renderer/chart_renderer'
import { Card } from "./card/card";
const actionRegistry = registry.category("actions");


const {onWillStart, useRef, onMounted, onWillUnmount, useState  } = owl;
class TrainingDashboard extends Component {

    async getTrainings(){
        const trainings = await this.orm.searchRead('termination.request', [['combined_state', 'in', ['approved', 'refused', 'processing']], ['create_date', '>', this.state.date]], ['combined_state']);
        const counts = { approved: 0, refused: 0, processing: 0 };

        trainings.forEach(training => {
            counts[training.combined_state]++;
        });
        this.state.trainings = {
            data: {
                labels: ['Approved', 'Refused', 'Processing'],
                datasets: [{
                    label: 'Training Status',
                    data: [counts.approved, counts.refused, counts.processing],
                    backgroundColor: [
                        'rgb(54, 162, 235)',
                        'rgb(255, 99, 132)',
                        'rgb(255, 205, 86)'
                    ],
                    hoverOffset: 4
                }]
            }
        }; 
      }

    setup() {

        this.state = useState({
            approved: {
                value: 10,
            }, 
            processing:{
                value: 10,
            }, 
            refused: {
                value: 10,
            }, 
            period:90,

        })
        super.setup()
        this.orm = useService('orm')
        this.actionService = useService('action')
       // this._fetch_data()
       this.getData()

       onWillStart(async ()=>{
        this.getDates()
        await this.getData()
        await this.getTrainings()

       })
    }

    async onChangePeriod(){
        this.getDates()
       await this.getData()
    }

    getDates(){
        this.state.date = moment().subtract(this.state.period, 'days').format('YYYY-MM-DD')

    }

    async getData(){
    
            const  approved= await this.orm.searchCount('termination.request', [['combined_state', 'in', ['approved']],  ['create_date', '>', this.state.date]])
            const  refused = await this.orm.searchCount('termination.request', [['combined_state', 'in', ['refused']], ['create_date', '>', this.state.date]] )
            const  processing= await this.orm.searchCount('termination.request', [['combined_state', 'in', ['processing']], ['create_date', '>', this.state.date]], )

        this.state.approved.value = approved
        this.state.refused.value = refused
        this.state.processing.value = processing

    }


    viewTermination(){
        let domain =  [['combined_state', 'in', ['approved']]]
        if(this.state.period > 0){
            domain.push(['create_date', '>', this.state.current_date])
        }
        this.actionService.doAction("hr_termination.employee_termination_action"), {
            additionalContext:{
                type: "ir.actions.act_window",
                name: "Accepted",
                res_model: "termination.request", 
                domain: domain,
                views: [[false, 'list'], [false, 'form']],

            }
        }

    }




    // _fetch_data(){
    //     var self = this;
    //     this.orm.call("hr.training", 'get_data', {}).then(function(result){
    //         $('#approved').append('<span>' + result.accepted + '</span>')
    //         $('#refused').append('<span>' + result.refused + '</span>')
    //         $('#taken').append('<span>' + result.taken + '</span>')

    //     })
    // }  
}

TrainingDashboard.template = "hr_termination.Dashboard";
TrainingDashboard.components = {ChartRenderer, Card}
actionRegistry.add("hr_termination.dashboard", TrainingDashboard);