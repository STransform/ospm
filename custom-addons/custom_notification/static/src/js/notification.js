/** @odoo-module **/

import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";

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
            showDropdown: false
        });

        this.orm = useService("orm");
        this.userService = useService("user"); 

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
    }

    async fetchNotifications() {
        try {
            const currentUserId = this.userService.userId; // Get current user ID
            const notifications = await this.orm.searchRead(
                "custom.notification",
                [["user_id", "=", currentUserId], ["is_read", "=", false]],
                ["id", "title", "message",'create_date']
            );

            this.state.notifications = notifications.map((notification) => ({
                ...notification,
                relativeTime: getRelativeTime(notification.create_date),
            }));
            this.state.unreadCount = notifications.length;
        } catch (error) {
            console.error("Failed to fetch notifications:", error);
        }
    }

    
    async markAsRead(notificationId) {
        try {
            await this.orm.write("custom.notification", [notificationId], { is_read: true });
            this.state.notifications = this.state.notifications.filter(
                (n) => n.id !== notificationId
            );
            this.state.unreadCount = this.state.notifications.length;
        } catch (error) {
            console.error("Failed to mark notification as read:", error);
        }
    }


    
    onClickNotification(notification) {
        this.markAsRead(notification.id);
        // Optionally perform additional actions
        console.log("Notification clicked:", notification);
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