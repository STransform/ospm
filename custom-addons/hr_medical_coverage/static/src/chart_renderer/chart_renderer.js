/**@odoo-module **/
import { registry } from "@web/core/registry";
import { Component } from  "@odoo/owl";
import { loadJS } from "@web/core/assets";
const {onWillStart, useRef, onMounted, onWillUnmount } = owl;


export class ChartRenderer extends Component {
   // ========== Properties ========== //
    setup() {
        this.chartRef = useRef('chart')
        onWillStart(async ()=>{
            await loadJS('https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js')
        })
        onMounted(()=>this.renderChart())
    }
    renderChart(){
        new Chart(
            this.chartRef.el,
            {
              type: this.props.type,
              data: this.props.config.data, 
              options: {
                responsive: true, 
                plugins:{
                    legend: {
                        position: 'bottom'
                    }
                }
              },
              title: {
                display: true, 
                text: this.props.title
              }
            }
          );
    } 
}

ChartRenderer.template = "hr_medical_coverage.ChartRenderer";