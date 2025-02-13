# Findminiapp
Scraper for www.findmini.app

## How to Set Up and Run findminiapp on GCP

1. **Enable Google Sheets and Google Drive API in GCP**
   Go to APIs & Services and press Enable APIs & Services. 
   Find the Google Sheets and Google Drive APIs.

2. **Modify compute-system.iam Service Account**  
   Add the Compute Engine Admin role (`roles/compute.admin`) to the `compute-system.iam` service account.  
   This allows it to create schedules and manage VMs.  

3. **Create a VM Instance**  
   Go to **Compute Engine** → **VM instances** → **Create Instance**.  
   Choose:  
   - **Machine type:** `e2-micro`  
   - **OS:** Ubuntu 22.04  
   - **Startup disk:** 10GB  

4. **Power on the VM**  
   Once created, start the VM.  

5. **Clone the Project into /opt Folder**  
   ```bash
   sudo apt update && sudo apt install -y git
   sudo git clone https://github.com/Gosugrag/findminiapp.git /opt/findminiapp
   ```

6. **Create a Service Account and Add Credentials**  
   - Go to **Google Cloud Console** → **IAM & Admin** → **Service Accounts**.  
   - Create a new service account.  
   - Generate a **JSON key file** and download it.  
   - Upload it to your project as `credentials.json` or copy the content and paste it into an existing `credentials.json`.  

7. **Add `startup.sh` as a Startup Script**  
   - Open **Compute Engine** → **VM settings** → **Edit** → **Metadata**.  
   - Add the contents of `startup.sh` in the **Startup Script** section.  

8. **Update the Email**  
   Edit the script file to replace the placeholder email with a **valid user email**.  

9. **Create a Schedule (Weekly or Monthly)**  
   - Go to **Instance Schedules** and create a weekly schedule and add a VM to it.  
   - Update schedule:  
   ```bash
   gcloud compute resource-policies update instance-schedule findminiapp-test \
       --region=us-central1 \
       --vm-start-schedule="15 13 * * *" \
       --vm-stop-schedule="15 14 * * *"
   ```

10. **Power off the VM**  

