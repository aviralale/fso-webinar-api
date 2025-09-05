
# 📖 Webinar API (Django + Djoser + Razorpay)

Base URL:

```
https://api-webinar.ctrlbits.com/
```

Authentication:

* Uses **JWT tokens** via Djoser.
* Include in headers:

  ```http
  Authorization: JWT <access_token>
  ```

---

## 🔑 Authentication (Auth)

### Register (Attendee/Host)

**POST** `/auth/users/`

Create a new user.

```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "attendee",
  "password": "StrongPass123!"
}
```

---

### Login (JWT Create)

**POST** `/auth/jwt/create/`

```json
{
  "username": "john_doe",
  "password": "StrongPass123!"
}
```

**Response Example**

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJh...",
  "access": "eyJ0eXAiOiJKV1QiLCJhb..."
}
```

---

### Refresh Token

**POST** `/auth/jwt/refresh/`

```json
{
  "refresh": "{{refreshToken}}"
}
```

---

### Get Current User

**GET** `/auth/users/me/`

---

### Update Current User

**PATCH** `/auth/users/me/`

```json
{
  "first_name": "Johnny",
  "last_name": "Doe"
}
```

---

### Set Password

**POST** `/auth/users/set_password/`

```json
{
  "new_password": "NewStrongPass123!",
  "current_password": "StrongPass123!"
}
```

---

### Reset Password

* **Request reset:**
  **POST** `/auth/users/reset_password/`

  ```json
  { "email": "john@example.com" }
  ```

* **Confirm reset:**
  **POST** `/auth/users/reset_password_confirm/`

  ```json
  {
    "uid": "<uid>",
    "token": "<token>",
    "new_password": "NewStrongPass123!"
  }
  ```

---

## 🎥 Webinars

### List Webinars

**GET** `/webinars/`

---

### Create Webinar (Admin Only)

**POST** `/webinars/`

Form-data fields:

* `title` (string)
* `description` (string)
* `start_time` (ISO datetime)
* `duration_minutes` (int)
* `capacity` (int)
* `price` (decimal)
* `host` (user ID)
* `image` (file, optional)

---

### Retrieve Webinar

**GET** `/webinars/:id/`

---

### Update Webinar (Host/Admin)

**PATCH** `/webinars/:id/`

```json
{
  "title": "Intro to DRF (Updated)",
  "price": 599.0
}
```

---

### Delete Webinar (Host/Admin)

**DELETE** `/webinars/:id/`

---

### Register for Webinar

**POST** `/webinars/register/`

```json
{
  "webinar_id": 1
}
```

---

### Verify Payment (Razorpay)

**POST** `/payments/verify/`

```json
{
  "razorpay_order_id": "order_ABC123",
  "razorpay_payment_id": "pay_DEF456",
  "razorpay_signature": "signature_789",
  "registration_id": 1
}
```

---

### Cancel Registration

**POST** `/registrations/:id/cancel/`

---

## 📊 Dashboard & Registrations

### Dashboard (Role-Aware)

**GET** `/dashboard/`

---

### My Registrations

**GET** `/registrations/my/`

---

### Webinar Attendees (Host/Admin)

**GET** `/webinars/:id/attendees/`

---

## 🔧 Environment Variables

| Key            | Value                               |
| -------------- | ----------------------------------- |
| `baseUrl`      | `https://api-webinar.ctrlbits.com/` |
| `accessToken`  | (set after login)                   |
| `refreshToken` | (set after login)                   |
