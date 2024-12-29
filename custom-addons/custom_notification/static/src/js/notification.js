/** @odoo-module **/

import { registry } from '@web/core/registry';
import { useService,actionService } from "@web/core/utils/hooks";

const { Component, onWillStart, useState, onMounted, onWillUnmount  } = owl;


function getRelativeTime(date) {
    const now = new Date();
    const past = new Date(date+"Z");
    const diffInMilliseconds = now - past;

    const seconds = Math.floor(diffInMilliseconds / 1000);
    const minutes = Math.floor(diffInMilliseconds / (1000 * 60));
    const hours = Math.floor(diffInMilliseconds / (1000 * 60 * 60));
    const days = Math.floor(diffInMilliseconds / (1000 * 60 * 60 * 24));

    if (seconds < 60) return `${seconds} seconds ago`;
    if (minutes < 60) return `${minutes} minutes ago`;
    if (hours < 24) return `${hours} hours ago`;
    return `${days} days ago`;
}

export class Notification extends Component {

	setup() {
        super.setup();
        // this.notifications = []
        this.state = useState({
            notifications: [],
            unreadCount: 0,
            showDropdown: false,
            limit: 5,          
            offset: 0,          
            hasMore: true  

        });

        this.orm = useService("orm");
        this.userService = useService("user"); 
        this.actionService = useService("action");

        onWillStart(async () => {
            await this.fetchNotifications();
        });

        // Add a click listener to handle clicks outside
        onMounted(() => {
            document.addEventListener("click", this.onOutsideClick);
        });

        // Remove the click listener when the component is destroyed
        onWillUnmount(() => {
            document.removeEventListener("click", this.onOutsideClick);
        });

        this.onClickNotification = this.onClickNotification.bind(this);
        this.onOutsideClick = this.onOutsideClick.bind(this);

    };

    async onClickNavbarMenu() {
        // Toggle the dropdown and fetch notifications when it is opened
        this.state.showDropdown = !this.state.showDropdown;
        if (this.state.showDropdown) {
            await this.fetchNotifications();
        }
        else{
            this.state.offset = 0;  // Reset the offset when the dropdown is closed
			this.state.hasMore = true; // Reset the hasMore when the dropdown is closed
        }
    }

    async fetchNotifications() {
        try {
            const currentUserId = this.userService.userId; // Get current user ID
            const all_notifications = await this.orm.searchRead(
                "custom.notification",
                [["user_id", "=", currentUserId], ["is_read", "=", false]],
                ["id", "title", "message",'create_date','action_model','action_id','action_res_id','action_view_mode','action_company_id'],
            );
            const notifications = await this.orm.searchRead(
                "custom.notification",
                [["user_id", "=", currentUserId], ["is_read", "=", false]],
                ["id", "title", "message",'create_date','action_model','action_id','action_res_id','action_view_mode','action_company_id'],
                { order: "create_date desc", limit: this.state.limit, offset: this.state.offset } // Order by create_date descending
            );

            this.state.notifications = notifications.map((notification) => ({
                ...notification,
                relativeTime: getRelativeTime(notification.create_date),
            }));
            this.state.unreadCount = all_notifications.length;

            // Check if more notifications exist
            if (notifications.length <= this.state.limit) {
                this.state.hasMore = false;
            }
        } catch (error) {
            console.error("Failed to fetch notifications:", error);
        }
    }

    async onClickSeeMore() {
        this.state.offset += this.state.limit;  // Increment the offset
        await this.fetchNotifications();        // Fetch the next set of notifications
    }
    
    async markAsRead(notificationId) {
        try {
            await this.orm.write("custom.notification", [notificationId], { is_read: true });
            this.state.showDropdown = false
            await this.fetchNotifications();
        } catch (error) {
            console.error("Failed to mark notification as read:", error);
        }
    }


    
    async onClickNotification(notification) {
        // mark as read notification
        await this.markAsRead(notification.id);

        // check if we have action to do
       
        if (notification.action_model && notification.action_res_id && notification.action_id && notification.action_view_mode && notification.action_company_id) {
            const baseUrl = window.location.origin + "/web";
            const params = new URLSearchParams({
                id: notification.action_res_id,
                cids: notification.action_company_id,
                action: notification.action_id,       
                model: notification.action_model,    
                view_type: notification.action_view_mode,        
            });

            // Final URL
            const redirectUrl = `${baseUrl}#${params.toString()}`;

            // Perform the redirection
            window.location.href = redirectUrl;
            console.log("the url is ===============+>",redirectUrl)
        } 
        
    }

    onOutsideClick(ev) {
        
        const dropdown = document.querySelector(".o_MessagingMenu_dropdownMenu");
        const toggleButton = document.querySelector(".o_NavbarMenu_toggler");
    
        // Ensure the dropdown is open and the clicked target is not inside the dropdown or the toggle button
        if (
            this.state.showDropdown &&
            !dropdown?.contains(ev.target) &&
            !toggleButton?.contains(ev.target)
        ) {
            this.state.showDropdown = false;
            this.state.offset = 0;
            this.state.hasMore = true;
        }
    }
    
}

// Assigning Template to class Component 
Object.assign(Notification, {
    template: 'Notification',
})

// Here I am adding our template in the navbar. To add in navbar, we have to add our template and 
// class in systray category, respectively.

registry.category('systray').add('custom_notification.Notification', { Component: Notification }, { sequence: 30 });