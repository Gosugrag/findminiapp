# Findminiapp
Scraper for www.findmini.app

## How to Set Up and Run findminiapp on GCP

1. **Modify compute-system.iam Service Account**  
   Add the Compute Engine Admin role (`roles/compute.admin`) to the `compute-system.iam` service account.  
   This allows it to create schedules and manage VMs.  

2. **Create a VM Instance**  
   Go to **Compute Engine** → **VM instances** → **Create Instance**.  
   Choose:  
   - **Machine type:** `e2-micro`  
   - **OS:** Ubuntu 22.04  
   - **Startup disk:** 10GB  

3. **Power on the VM**  
   Once created, start the VM.  

4. **Clone the Project into /opt Folder**  
   ```bash
   sudo apt update && sudo apt install -y git
   sudo git clone https://github.com/Gosugrag/findminiapp.git /opt/findminiapp
   ```

5. **Create a Service Account and Add Credentials**  
   - Go to **Google Cloud Console** → **IAM & Admin** → **Service Accounts**.  
   - Create a new service account.  
   - Generate a **JSON key file** and download it.  
   - Upload it to your project as `credentials.json` or copy the content and paste it into an existing `credentials.json`.  

6. **Add `startup.sh` as a Startup Script**  
   - Open **Compute Engine** → **VM settings** → **Edit** → **Metadata**.  
   - Add the contents of `startup.sh` in the **Startup Script** section.  

7. **Update the Email**  
   Edit the script file to replace the placeholder email with a **valid user email**.  

8. **Create a Schedule (Weekly or Monthly)**  
   - Go to **Instance Schedules** and create a weekly schedule and add a VM to it.  
   - Update schedule:  
   ```bash
   gcloud compute resource-policies update instance-schedule findminiapp-test \
       --region=us-central1 \
       --vm-start-schedule="15 13 * * *" \
       --vm-stop-schedule="15 14 * * *"
   ```

9. **Power off the VM**  

