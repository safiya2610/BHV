# TODO: Fix Google OAuth Authentication Errors

## Tasks
- [x] Update auth_google.py: Remove api_base_url from client_kwargs to avoid relative URL issues.
- [x] Update app/services/auth_service.py: Pass state="" to authorize_redirect to disable state checking in development.
- [x] Update app/services/auth_service.py: Change oauth.google.get to use full URL "https://www.googleapis.com/oauth2/v2/userinfo" instead of relative "userinfo".
