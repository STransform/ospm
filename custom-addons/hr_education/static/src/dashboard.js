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
        const trainings = await this.orm.searchRead('hr.training', [['state', 'in', ['approved', 'refused', 'taken']], ['create_date', '>', this.state.date]], ['state']);
        const counts = { approved: 0, refused: 0, taken: 0 };

        trainings.forEach(training => {
            counts[training.state]++;
        });
        this.state.trainings = {
            data: {
                labels: ['Approved', 'Refused', 'Taken'],
                datasets: [{
                    label: 'Training Status',
                    data: [counts.approved, counts.refused, counts.taken],
                    backgroundColor: [
                        'rgb(54, 162, 235)',
                        'rgb(255, 99, 132)',
                        'rgb(255, 205, 86)'
                    ],
                    hoverOffset: 4
                }]
            }
        };
        // const data = await this.orm.readGroup('hr.training', [['state', 'in', ['approved']], ['create_date', '>', this.state.date]], ['type'], ['type'])
        // this.state.trainings = {
        //   data: {
        //     labels: [
        //         'Red',
        //         'Blue',
        //         'Yellow'
        //       ],
        //       datasets: [{
        //         label: 'My First Dataset',
        //         data: [300, 50, 100],
        //         backgroundColor: [
        //           'rgb(255, 99, 132)',
        //           'rgb(54, 162, 235)',
        //           'rgb(255, 205, 86)'
        //         ],
        //         hoverOffset: 4
        //       }]
        //   }
        // } 
      }

    setup() {

        this.state = useState({
            approved: {
                value: 10,
            }, 
            taken:{
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
        //if(this.state.period > 0){
            const  approved= await this.orm.searchCount('hr.training', [['state', 'in', ['approved']],  ['create_date', '>', this.state.date]])
            const  refused = await this.orm.searchCount('hr.training', [['state', 'in', ['refused']], ['create_date', '>', this.state.date]] )
            const  taken= await this.orm.searchCount('hr.training', [['state', 'in', ['taken']], ['create_date', '>', this.state.date]], )
       // }
            // const  approved= await this.orm.searchCount('hr.training', [['state', 'in', ['approved']]])
            // const  refused = await this.orm.searchCount('hr.training', [['state', 'in', ['refused']]] )
            // const  taken= await this.orm.searchCount('hr.training', [['state', 'in', ['taken']]], )
           
      
        this.state.approved.value = approved
        this.state.refused.value = refused
        this.state.taken.value = taken

    }


    viewTrainings(){
        let domain =  [['state', 'in', ['approved']]]
        if(this.state.period > 0){
            domain.push(['create_date', '>', this.state.current_date])
        }
        this.actionService.doAction("hr_training.hr_training_action"), {
            additionalContext:{
                type: "ir.actions.act_window",
                name: "Accepted",
                res_model: "hr.training", 
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

TrainingDashboard.template = "hr_training.Dashboard";
TrainingDashboard.components = {ChartRenderer, Card}
actionRegistry.add("hr_training.dashboard", TrainingDashboard);