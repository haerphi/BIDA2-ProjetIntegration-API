# Endpoints

## Authentication

- POST /api/token/ : Obtenir un jeton d'accès et un jeton de rafraîchissement (Login)
  - Requête :

  ```json
  {
    "affiliation_number": "1234567",
    "password": "password"
  }
  ```

  - Réponse :

  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

- POST /api/token/refresh/ : Rafraîchir le jeton d'accès
  - Requête :

  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

  - Réponse :

  ```json
  {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

## Members

- GET /api/members/ : List all members (authenticated)
  - Query parameters :
    - ranking : Filter by ranking
    - gender : Filter by gender
    - is_active : Filter by active status
    - affiliation_number : Filter by affiliation number
    - email : Filter by email
    - firstname : Filter by firstname
    - lastname : Filter by lastname
    - postal_code : Filter by postal code
    - country : Filter by country
    - phone : Filter by phone
    - birth_date : Filter by birth date
    - category : Filter by category
    - ordering : Sort by field (e.g., lastname, ranking)
  - Response :

  ```json
  [
    {
      "id": 1,
      "user": 1,
      "firstname": "John",
      "lastname": "Doe",
      "email": "[EMAIL_ADDRESS]",
      "created_at": "2022-01-01T00:00:00Z",
      "role": "member"
    }
  ]
  ```

  (the email is returned only if the requester is an admin)

- GET /api/members/<id>/ : Retrieve a member (authenticated)
  - Path parameters :
    - id : The UUID of the member to retrieve
  - Response :

  ```json
  {
    "id": 1,
    "user": 1,
    "firstname": "John",
    "lastname": "Doe",
    "email": "[EMAIL_ADDRESS]",
    "street": "123 Main St",
    "city": "New York",
    "postal_code": "12345",
    "country": "USA",
    "phone": "123456789",
    "birth_date": "2000-01-01",
    "gender": "male",
    "affiliation_number": "1234567",
    "ranking": "A",
    "is_active": true,
    "created_at": "2022-01-01T00:00:00Z",
    "role": "member"
  }
  ```

  (the email is returned only if the requester is an admin)

- POST /api/members/ : Create a member (admin only)
  - Request :

  ```json
  {
    "firstname": "John",
    "lastname": "Doe",
    "email": "[EMAIL_ADDRESS]",
    "street": "123 Main St",
    "city": "New York",
    "postal_code": "12345",
    "country": "USA",
    "phone": "123456789",
    "birth_date": "2000-01-01",
    "gender": "male",
    "affiliation_number": "1234567",
    "ranking": "A",
    "is_active": true,
    "password": "password"
  }
  ```

- PUT /api/members/<id>/ : Update a member (admin only)
  - Path parameters :
    - id : The UUID of the member to update
  - Request :

  ```json
  {
    "firstname": "John",
    "lastname": "Doe",
    "email": "[EMAIL_ADDRESS]",
    "street": "123 Main St",
    "city": "New York",
    "postal_code": "12345",
    "country": "USA",
    "phone": "123456789",
    "birth_date": "2000-01-01",
    "gender": "male",
    "affiliation_number": "1234567",
    "ranking": "A",
    "is_active": true
  }
  ```

- PUT /api/members/me/ : Update the logged-in member's profile
  - Request :

  ```json
  {
    "firstname": "John",
    "lastname": "Doe",
    "email": "[EMAIL_ADDRESS]",
    "street": "123 Main St",
    "city": "New York",
    "postal_code": "12345",
    "country": "USA",
    "phone": "123456789",
    "birth_date": "2000-01-01",
    "gender": "male"
  }
  ```

- PATCH /api/members/<id>/ : Partial update of a member (admin only)
  - Path parameters :
    - id : The UUID of the member to update
  - Request :

  ```json
  {
    "role": "admin",
    "is_active": true
  }
  ```

- DELETE /api/members/<id>/ : Delete a member (admin only)
  - Path parameters :
    - id : The UUID of the member to delete
- DELETE /api/members/me/ : Delete the logged-in member's profile
- PATCH /api/members/<id>/set_password/ : Set a member's password (admin only)
  - Path parameters :
    - id : The UUID of the member to update
  - Request :

  ```json
  {
    "password": "password"
  }
  ```

- PATCH /api/members/me/set_password/ : Set the logged-in member's password
  - Request :

  ```json
  {
    "password": "password"
  }
  ```

- GET /api/members/me/ : Retrieve the logged-in member's profile

## Courts

- GET /api/courts/ : List all courts (authenticated)
  - Response :

  ```json
  [
    {
      "id": 1,
      "number": 1
    }
  ]
  ```

- GET /api/courts/<id>/ : Retrieve a court (authenticated)
  - Response :

  ```json
  {
    "id": 1,
    "number": 1
  }
  ```

- POST /api/courts/ : Create a court (admin only)
  - Request :

  ```json
  {
    "number": 1
  }
  ```

- PUT /api/courts/<id>/ : Update a court (admin only)
  - Request :

  ```json
  {
    "number": 2
  }
  ```

- PATCH /api/courts/<id>/ : Partial update of a court (admin only)
  - Request :

  ```json
  {
    "number": 2
  }
  ```

- DELETE /api/courts/<id>/ : Delete a court (admin only)

- POST /api/courts/<id>/book : Book a court for one or two hours
  - Request :

  ```json
  {
    "court_id": 1,
    "members": [2, 3, 4],
    "date_time": "2026-04-18T12:00",
    "duration": 60
  }
  ```
