# Download Google photos

### Required Python Packages

1. Google search for "sheets api python". Go to https://developers.google.com/sheets/api/quickstart/python

    pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
    pip install pandas

2. Copied Google.py from https://learndataanalysis.org/getting-started-with-google-photos-api-and-python-part-1/

### Documentation

https://developers.google.com/photos -> Guides


### Create Google Project and Credentials

Page: https://console.cloud.google.com/

1. "select a project" -> create new project

2. On this new project dashboard, on the menu on the left side, click "API & Services -> Library",
search for "photos library api". Click on the Photos Library API and "Enable". If it is already enabled,
click on "manage". You can see quotas, credentials, and limits.

3. Assume there is no credentials for Photos Lib API yet. On the left side menu, click on "Home",
then "API & Services -> Credentials". "Create Credentials -> OAuth client ID". You may need to create
an "OAuth consent screen". Create a new credential for "Desktop App". Download the credential JSON file.

4. To work in different account, you need to remove "token_photoslibrary_v1.pickle" or point it at different
pickle files. If "token_photoslibrary_v1.pickle" does not exist, it will create one by asking you to choose
account on Google website

### Albums

https://developers.google.com/photos/library/reference/rest

