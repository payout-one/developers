# FraudNet API Documentation

## Overview

FraudNet is a real-time fraud detection API that predicts the likelihood of fraudulent transactions using a two-stage machine learning approach combining autoencoder-based anomaly detection with XGBoost classification.

**API Version:** v1

---

## Authentication

All API endpoints require OAuth2 authentication with the `fraudnet` scope.

### Authorization Header

Include the access token in the Authorization header for all requests:

```
Authorization: Bearer <your_access_token>
```

### Required Scope

- `fraudnet` - Required for all FraudNet API operations

### Obtaining Access Tokens

Contact your system administrator or refer to your OAuth2 provider documentation for instructions on obtaining access tokens with the `fraudnet` scope.

### Authentication Errors

| Status Code | Error        | Description                                       |
|-------------|--------------|---------------------------------------------------|
| 401         | Unauthorized | Missing or invalid access token                   |
| 403         | Forbidden    | Token does not have the required `fraudnet` scope |

---

## Endpoints

### Health Check

Check the health and availability of the FraudNet service.

**Endpoint:** `GET /api/v1/health`

**Authentication:** Required (OAuth2 with `fraudnet` scope)

**Request:**
```bash
curl -X GET https://api.example.com/api/v1/health \
  -H "Authorization: Bearer <your_access_token>"
```

**Response:**
```json
{
  "status": "healthy",
  "service": "fraudnet-api",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK` - Service is healthy
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions

---

### Predict Fraud

Predict the fraud probability for a specific transaction.

**Endpoint:** `POST /api/v1/predict`

**Authentication:** Required (OAuth2 with `fraudnet` scope)

**Request Body:**
```json
{
  "txn_id": "string"
}
```

**Parameters:**

| Field  | Type   | Required | Description                   |
|--------|--------|----------|-------------------------------|
| txn_id | string | Yes      | Unique transaction identifier |

**Request Example:**
```bash
curl -X POST https://api.example.com/api/v1/predict \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "txn_id": "123456"
  }'
```

**Response:**
```json
{
  "txn_id": "123456",
  "fraud_probability": 0.8542,
  "is_fraud": true,
  "anomaly_score": 2.3456,
  "prediction_timestamp": "2026-03-18T10:30:45.123Z"
}
```

**Response Fields:**

| Field                | Type    | Description                         |
|----------------------|---------|-------------------------------------|
| txn_id               | string  | Transaction identifier from request |
| fraud_probability    | float   | Probability of fraud (0.0 to 1.0)   |
| is_fraud             | boolean | Binary fraud classification         |
| anomaly_score        | float   | Autoencoder reconstruction error    |
| prediction_timestamp | string  | ISO 8601 timestamp of prediction    |

**Status Codes:**
- `200 OK` - Prediction successful
- `400 Bad Request` - Invalid request body or missing txn_id
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Transaction ID not found in database
- `500 Internal Server Error` - Model inference or database error

**Error Response:**
```json
{
  "detail": "Transaction ID not found"
}
```
