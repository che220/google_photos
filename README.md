# Download Google photos

https://developers.google.com/photos -> Guides


https://console.cloud.google.com/:

1. "select a project" -> create new project

2. On this new project dashboard, on the menu on the left side, click "API & Services -> Library", search for "photos library api". Click on the Photos Library API and "Enable". If it is already enabled, click on "manage". You can see quotas, credentials, and limits.

3. Assume there is no credentials for Photos Lib API yet. On the left side menu, click on "Home", then "API & Services -> Credentials". "Create Credentials -> OAuth client ID". You may need to create an "OAuth consent screen". Create a new credential for "Desktop App". Download the credential JSON file.

4. Google search for "sheets api python". Go to https://developers.google.com/sheets/api/quickstart/python
    pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
    pip install pandas

    Now Google Photos Library enabled

5. Copied Google.py from https://learndataanalysis.org/getting-started-with-google-photos-api-and-python-part-1/

### Albums

Reference here:

    https://developers.google.com/photos/library/reference/rest

