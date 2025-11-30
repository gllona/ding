# DING - Raspberry Pi 4 Full Setup with Internet Access and HTTPS

Follow this hand-crafted guide to set up Ding in a Raspberry Pi 4.  

From anywhere in the Internet, you will be able to securely log in to Ding and send print jobs to your printer.

## What You Need

- Raspberry Pi 4 with Raspberry Pi OS (64-bit) installed (no monitor or keyboard needed, but `sudo` access needed)
- Linux-compatible USB Thermal Receipt Printer
- USB cable for the printer
- Domestic Internet router with public, dynamic IP address set by your Internet provider
- Your router's webadmin interface user and password
- A domain name or subdomain
- Access to the web console of your DNS provider for your domain
- A PC where you can open an SSH session to your Raspberry Pi
- The Raspberry Pi and the PC must be connected to the router's LAN

For Ding:

- A SendGrid account
- A SendGrid API key (get it after you create your SendGrid account)
- An email address from which to send the authentication emails to the users

## Domain / Subdomain Setup

In this guide we will use a subdomain name for Ding: `ding.example.com`.

We will use the FreeDNS service https://freedns.afraid.org/ to set up dynamic DNS for our Raspberry Pi.

Our example top level domain `example.com` is already configured with the DNS records of the FreeDNS service.

## Check the Router's Public IP Address

1. Open https://www.whatismyip.com/ in your browser
2. Copy the public IP address
3. Open the router's webadmin interface
4. Check the router's public IP address is the same as the public IP address you copied in step 2

If step 4 answer is a `no`, then you need to ask your ISP for a public (dynamic) IP address that is not behind DNS masquerading. That will allow incoming Internet traffic to your router.

## Setting up FreeDNS

1. Open https://freedns.afraid.org/ in your browser
2. Create a free account
3. In `Domains`, add your domain `example.com` to the FreeDNS service
4. In `Subdomains`, add the subdomain `ding.example.com` to the FreeDNS service
5. Go to the `Dynamic DNS` tab
6. For your subdomain, click on `Quick cron example` and copy the non-commented lines of the file. That should be like:
    ```
    PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
    
    4,9,14,19,24,29,34,39,44,49,54,59 * * * * sleep 53 ; wget --no-check-certificate -O - https://freedns.afraid.org/dynamic/update.php?MDcw_REDACTED_ODA2 >> /tmp/freedns_ding_example_com.log 2>&1 &
    ```

For the DNS settings needed by SendGrid, you can also use the FreeDNS service to add the `CNAME` and `TXT` records to your subdomain.

## Set up the Router

Get the LAN IP address of the Raspberry Pi:

1. Open an SSH session to the Raspberry Pi
2. Run `hostname -I | awk '{print $1}'` and copy the IP address

Set the IP address for the Raspberry Pi as static:

1. Open the router's webadmin interface
2. Go to the `DHCP` tab
3. Add a new DHCP reservation:
    - IP Address: The IP address of your Raspberry Pi
    - MAC Address: The MAC address of your Raspberry Pi (you can find it in the router's UI under `Connected Devices`)

Port forwarding:

1. Open the router's webadmin interface
2. Go to the `Port Forwarding` tab (can be under options `Internet`, `Internet > Security`, etc.)
3. Add a new port forwarding rule for the Ding UI:
    - Protocol: TCP
    - External Port: 8501
    - Internal Port: 8501
    - Internal IP Address: The static LAN IP address of your Raspberry Pi
4. Add a new port forwarding rule for the Ding API:
    - Protocol: TCP
    - External Port: 8508
    - Internal Port: 8508
    - Internal IP Address: The static LAN IP address of your Raspberry Pi
 
## Upgrade your Raspberry Pi OS

1. Open an SSH session to the Raspberry Pi
2. Run `sudo apt update && sudo apt upgrade -y`

## Set up a new Raspberry Pi User

For security purposes, we will set up Ding under a separate, unprivileged Linux user in the Raspberry Pi that have access to the printer only.

1. Open an SSH session to the Raspberry Pi
2. Run `sudo useradd -m -s /bin/bash -g lp ding`
3. Run `sudo passwd ding` and set a password for the user (optional step)

## Complete Dynamic DNS Setup

1. Open an SSH session to the Raspberry Pi
2. Run `sudo su - ding` to connect as the new user
3. Run `crontab -e` and add the cron job for the dynamic DNS update (from the last step of `Setting up FreeDNS` section). Just paste the lines at the end of the file

## Get the Thermal Printer USB ID's

1. Disconnect the printer from the Raspberry Pi
2. Open an SSH session to the Raspberry Pi
3. Run `lsusb` and save the output
4. Run `ls -l /dev/usb`. The output should show no devices
5. Connect the printer to the Raspberry Pi and turn it on
6. Run `lsusb` and save the output
7. Compare the outputs of the two `lsusb` commands and find the new line with the vendor and product IDs of the printer. Example for Netum NT-1809DD/NT-1809 Mini Thermal Printer:
    ```
    Bus 001 Device 089: ID 0416:5011 Winbond Electronics Corp. Virtual Com Port
    ```
    The vendor ID is `0x0416` and the product ID is `0x5011`.
8. Run `ls -l /dev/usb`. The output should be like:
    ```
    crw-rw---- 1 root lp 180, 0 Nov 30 12:50 lp0
    ```
    The device path is `/dev/usb/lp0`.

## Set up Ding

1. Open an SSH session to the Raspberry Pi
2. Run `sudo su - ding` to connect as the new user
3. Run `git clone https://github.com/gorka/ding.git` to clone the repository
4. Go to the Ding directory with `cd ding`
5. Run the setup script: `./setup.sh`   
6. Edit the newly created `.env` file and fill in the values (you need to define your own Ding API key). Note: Use your public subdomain like `APP_URL=http://ding.example.com:8501`

## Set up the First Ding User

Run the Ding API:

1. Open an SSH session to the Raspberry Pi
2. Run `sudo su - ding` to connect as the new user
3. Go to the Ding directory with `cd ding`
4. Run `./run_api.sh`

Create the first user:

1. Open another SSH session to the Raspberry Pi
2. Install `curl` with `sudo apt install curl`
3. Run `curl -X POST http://localhost:8508/api/users -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" -d '{"username": "rocky", "email": "rockydog@example.com"}'` to create the first user (replace the username and the email values)

## Run the Ding UI

1. Open an SSH session to the Raspberry Pi
2. Run `sudo su - ding` to connect as the new user
3. Go to the Ding directory with `cd ding`
4. Run `./run_ui.sh`

## Ding something!

1. Open your browser and go to `http://ding.example.com:8501`
2. Log in with the first user you created (e.g. "rocky")
3. Go to the "Text Message" tab
4. Type your message
5. Select font size (small/medium/large)
6. Choose format (Plain or Cowsay)
7. Click "SEND TO PRINTER"

The printer should print your message!

## Automatic Ding Start

Open an SSH session to the Raspberry Pi.

Use `nano` or `vi` to create the service files (we will use `vi` in this guide, but `nano` can be easier to use):

Run `sudo vi /etc/systemd/system/ding-api.service` and add the following content:

```ini
[Unit]
Description=DING API
After=network.target

[Service]
Type=simple
User=ding
WorkingDirectory=/home/ding/ding
ExecStart=/home/ding/ding/run_api.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

Run `sudo vi /etc/systemd/system/ding-ui.service` and add the following content:

```ini
[Unit]
Description=DING UI
After=network.target

[Service]
Type=simple
User=ding
WorkingDirectory=/home/ding/ding
ExecStart=/home/ding/ding/run_ui.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ding-api ding-ui
sudo systemctl start ding-api ding-ui
```

Check the status:

```bash
systemctl status ding-api ding-ui
```

Both services should be up and running.

## HTTPS Setup with nginx and certbot

We will use port `8543` for the HTTPS traffic as the HTTPS standard port `443` is already used by another service in my LAN. However, if it's not your case, it is better to use port `443` because your public URL will be like `https://ding.example.com`.

First of all, set up a port forwarding rule in your router's webadmin interface to forward port `8543` to the Raspberry Pi's IP address.

Also, set up a temporary port forwarding rule in your router to forward port `80` to the Raspberry Pi.

Finally, edit `.env` and set the port to `8543`:

```
APP_URL=http://ding.example.com:8543
```

After that, restart the Ding UI with `sudo systemctl restart ding-ui`.

Now, it is time to set up `nginx`:

1. Open an SSH session to the Raspberry Pi
2. Install `nginx` reverse proxy with `sudo apt install nginx -y`.
3. Disable the default `nginx` site with `sudo rm /etc/nginx/sites-enabled/default`
4. Create a nginx server configuration with `sudo vi /etc/nginx/sites-available/ding.example.com`. Add this content to the file:
    ```
    server {
        listen 8543;
        server_name ding.example.com;
    
        location /api {
            proxy_pass http://0.0.0.0:8508;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    
        location / {
            proxy_pass http://0.0.0.0:8501/;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $http_host;
            proxy_redirect off;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
    ```
5. Enable the new site with `sudo ln -s /etc/nginx/sites-available/ding.example.com /etc/nginx/sites-enabled/ding.example.com`
6. Test the configuration with `sudo nginx -t`
7. Restart `nginx` with `sudo systemctl restart nginx`
8. From your browser, check if the site is working by going to `http://ding.example.com:8543`

Get the SSL certificate:

1. Install `certbot` with `sudo apt install certbot python3-certbot-nginx -y`
2. Edit the nginx server configuration with `sudo vi /etc/nginx/sites-available/ding.example.com` and replace the port number with other unused port number like `8999`. Example:
    ```
    server {
        listen 8999;
        server_name ding.example.com;
        ...
    ```
3. Restart `nginx` with `sudo systemctl restart nginx`
4. Get a free SSL certificate with `sudo certbot --nginx --https-port 8543`:
    - Select your subdomain name by number, e.g. `1` for `ding.example.com`
    - Wait for `certbot` to complete the process, It will modify the `nginx` configuration file
5. Edit the nginx server configuration with `sudo vi /etc/nginx/sites-available/ding.example.com` and delete the line that says `listen 8999;`
6. Restart `nginx` with `sudo systemctl restart nginx`
7. Edit `.env` and set the protocol to `https`: `APP_URL=https://ding.example.com:8543`
8. Restart the Ding UI with `sudo systemctl restart ding-ui`.
9. From your browser, check if the site is working with HTTPS by going to `https://ding.example.com:8543`

After that, you can remove the temporary port forwarding rule (port `80`) in your router. Also, you can remove the port forwarding rules for ports `8501` and `8508`, as now all HTTPS traffic will enter in port `8543`. Such a case you remove them, the Postman API collection requires to add the `/api` prefix for all endpoints related to user administration, etc.

