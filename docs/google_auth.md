# Google Authentication Integration

This document outlines the steps taken to implement Google Single Sign-On (SSO) for existing members in the API.

## Requirements and Flow

- The feature allows users who have already been registered by an admin to log in using their Google account.
- The workflow expects the frontend to supply a Google `id_token`.
- The backend verifies the token with Google, extracts the email, and returns standard JWT access and refresh tokens if the email matches a registered member.
- If the email does not match any active user, a `401 Unauthorized` response is returned.

## Steps Performed

### 0. Create Google OAuth2 Client ID

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Go to the product "APIs & Services" > "OAuth consent screen".
4. "Get Started" and fill in the required information.
   - App Information name: "BIDA2-tennis-club-Auth"
   - User support email: [EMAIL_ADDRESS]"
   - Select "External" User Type. (so anyone can use it and not only company users)
   - Create
5. Go to the product "APIs & Services" > "Credentials".
6. Click + Create Credentials at the top and select OAuth client ID.
7. Select "Web application" as the application type.
8. Add the "Authorized JavaScript origins": http://localhost:5173
9. Click Create.
10. Download the JSON file and save it somewhere VERY safe.
11. Copy the Client ID and paste it in the .env file.

### 1. Dependency Installation

Added the necessary Python libraries to verify Google tokens securely against Google's servers.

```bash
poetry add google-auth requests
```

### 2. Environment Configuration

Updated the configuration to track the required Google Client ID.

**`.env` & `.env.example`**
Added the environment variable tracking the Client ID:

```env
GOOGLE_CLIENT_ID=your_client_id_here
```

**`src/core/settings/base.py`**
Configured Django Settings to read this variable gracefully:

```python
GOOGLE_CLIENT_ID = env('GOOGLE_CLIENT_ID', default='')
```

### 3. API View Implementation (`src/core/views.py`)

Created the serialization and view logic for validating the Google tokens.

- **`GoogleLoginSerializer`**: Exposes the schema for DRF Spectacular so the Swagger UI knows it requires a `token` field.
- **`GoogleLoginView`**:
  - Parses and validates `token` from the request body.
  - Utilizes `google.oauth2.id_token.verify_oauth2_token` to cryptographically validate the token against your application's `GOOGLE_CLIENT_ID`.
  - Extracts the requested user `email`.
  - Lookups `User.objects.filter(email=email).first()`.
  - Rejects connections (`401 Unauthorized`) if no registered and active user is found.
  - Generates the standard API `access` and `refresh` tokens using SimpleJWT's `RefreshToken.for_user(user)` if successful.

### 4. URL Routing (`src/core/urls.py`)

Exposed the new view via a dedicated endpoint.

```python
from .views import GoogleLoginView

urlpatterns = [
    # ...
    path('api/token/google/', GoogleLoginView.as_view(), name='token_obtain_google'),
    # ...
]
```

## Next Steps for the Frontend / Administrator

1. Generate an OAuth2 Client ID from the [Google Cloud Console](https://console.cloud.google.com/).
2. Place the generated Client ID in your local backend `.env` file under `GOOGLE_CLIENT_ID`.
3. In the frontend client, implement Google Login, obtain the ID token, and send a `POST` request to `/api/token/google/` with `{ "token": "<your-google-id-token>" }`.
