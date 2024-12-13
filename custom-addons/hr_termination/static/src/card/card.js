/** @odoo-module */

const {Component} = owl;

export class Card extends Component{
}

Card.template = "hr_termination.Card"
Card.Props = {
    slots: {
        type: Object, 
        shape: {
            default: Object, 
            title: { type: Object, optional: true}
        },
    }, 

    className: {
        type: String,
        optional: true,
    }
}