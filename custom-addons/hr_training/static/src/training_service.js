/** @odoo-module */
import { registry } from "@web/core/registry";
import { memoize } from "@web/core/utils/functions"; // this is used to caching functions

/** 
 * this is step 3 of creating the caching service to make rpc call for specific routes 
*/

export const TrainingService = {
    dependencies: ["rpc"] , // including the dependecies of this service
    async: ['loadStatistics'], 
    start(env, { rpc }) {
        return {
            loadStatistics: memoize(() => rpc("/hr_training/statistics"))
        }
    }
}
registry.category("services").add("trainingService", TrainingService); // registering this caching service as a service