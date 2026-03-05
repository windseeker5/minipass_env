My VPS Structure:

  1. /home/kdresdell/minipass_env/ - Main infrastructure directory
    - Contains main docker-compose.yml (nginx-proxy, mailserver, SSL)
    - Contains MinipassWebSite/ - your main website/onboarding Flask app
  2. /home/kdresdell/minipass_env/app/ - Git submodule (dpm.git repository)
    - This is the template/source code for the Minipass application
    - This is what customers are buying (Digital Pass Manager)
    - This should be the latest code used for upgrading customers
  3. /home/kdresdell/minipass_env/deployed/*/app/ - Customer instances
    - Each customer gets a copy of the /minipass_env/app/ code
    - Each has their own container and data