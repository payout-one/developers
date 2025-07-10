# Transaction Splitting for Insurance Companies

## Overview

Transaction splitting allows insurance companies to automatically split incoming payments into multiple transaction records based on product `offer_id` values. This enables separate tracking and reporting for different insurance products (MTPL, CASCO, etc.) within a single payment.

## How It Works

When transaction splitting is enabled:
1. **One Payment** creates **Multiple Transactions** (one per unique offer_id)
2. Each transaction includes the offer_id for separate tracking
3. All money goes to your account regardless of offer_id
4. Split routing rules can be configured for automatic payouts

## Enabling Transaction Splitting

Two conditions must be met:
1. **Account Feature**: Contact support to enable transaction splitting on your account
2. **Checkout Flag**: Set `should_split: true` in your checkout request

## Product Configuration

Products must include an `offer_id` field to enable splitting:

```json
{
  "products": [
    {
      "name": "MTPL Basic",
      "offer_id": "MTPL",
      "unit_price": 100.00,
      "quantity": 1
    },
    {
      "name": "CASCO Premium",
      "offer_id": "CASCO",
      "unit_price": 200.00,
      "quantity": 1
    }
  ],
  "should_split": true
}
```

## Webhook Response

Payment webhooks include split transaction information:

```json
{
  "external_id": "checkout_123",
  "object": "webhook",
  "type": "payment",
  "data": {
    "payment": {
      "id": "pay_456",
      "amount": 30000,
      "currency": "RON",
      "status": "successful",
      "split_transactions": [
        {
          "transaction_id": "txn_789",
          "amount": 10000,
          "offer_id": "MTPL"
        },
        {
          "transaction_id": "txn_790",
          "amount": 20000,
          "offer_id": "CASCO"
        }
      ]
    }
  }
}
```

## Split Routing Configuration

Configure automatic payout routing through the merchant dashboard or API:

```json
{
  "split_routing_rules": [
    {
      "offer_id": "MTPL",
      "iban": "RO23CITI0000000000000001",
      "bank_name": "Citi Bank Romania",
      "description": "MTPL Insurance Products"
    },
    {
      "offer_id": "CASCO",
      "iban": "RO23BTRL0000000000000001",
      "bank_name": "Banca Transilvania",
      "description": "CASCO Insurance Products"
    }
  ]
}
```

### API Endpoints

Manage split routing rules via API:

- `GET /api/v1/split_routing_rules` - List rules
- `POST /api/v1/split_routing_rules` - Create rule
- `PUT /api/v1/split_routing_rules/:id` - Update rule
- `DELETE /api/v1/split_routing_rules/:id` - Delete rule

#### List Split Routing Rules

```bash
GET /api/v1/split_routing_rules
Authorization: Bearer your_api_token
```

**Response:**
```json
{
  "data": [
    {
      "id": "rule_123",
      "offer_id": "MTPL",
      "iban": "RO23CITI0000000000000001",
      "bank_name": "Citi Bank Romania",
      "description": "MTPL Insurance Products",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "rule_124",
      "offer_id": "CASCO",
      "iban": "RO23BTRL0000000000000001",
      "bank_name": "Banca Transilvania",
      "description": "CASCO Insurance Products",
      "created_at": "2024-01-15T10:35:00Z",
      "updated_at": "2024-01-15T10:35:00Z"
    }
  ]
}
```

#### Create Split Routing Rule

```bash
POST /api/v1/split_routing_rules
Authorization: Bearer your_api_token
Content-Type: application/json
```

**Request Body:**
```json
{
  "offer_id": "MTPL",
  "iban": "RO23CITI0000000000000001",
  "bank_name": "Citi Bank Romania",
  "description": "MTPL Insurance Products"
}
```

**Response:**
```json
{
  "data": {
    "id": "rule_125",
    "offer_id": "MTPL",
    "iban": "RO23CITI0000000000000001",
    "bank_name": "Citi Bank Romania",
    "description": "MTPL Insurance Products",
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

#### Update Split Routing Rule

```bash
PUT /api/v1/split_routing_rules/rule_125
Authorization: Bearer your_api_token
Content-Type: application/json
```

**Request Body:**
```json
{
  "iban": "RO23CITI0000000000000002",
  "bank_name": "Citi Bank Romania - Updated",
  "description": "Updated MTPL Insurance Products"
}
```

**Response:**
```json
{
  "data": {
    "id": "rule_125",
    "offer_id": "MTPL",
    "iban": "RO23CITI0000000000000002",
    "bank_name": "Citi Bank Romania - Updated",
    "description": "Updated MTPL Insurance Products",
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:30:00Z"
  }
}
```

#### Delete Split Routing Rule

```bash
DELETE /api/v1/split_routing_rules/rule_125
Authorization: Bearer your_api_token
```

**Response:**
```json
{
  "message": "Split routing rule deleted successfully"
}
```

#### Error Responses

**400 Bad Request:**
```json
{
  "errors": {
    "offer_id": ["can't be blank"],
    "iban": ["is invalid"]
  }
}
```

**404 Not Found:**
```json
{
  "error": "Split routing rule not found"
}
```

**409 Conflict:**
```json
{
  "error": "A rule for this offer_id already exists"
}
```

### Dashboard Management

Access the "Split Routing" section in your merchant dashboard to:
- Create/Edit/Delete routing rules
- View split transaction history
- Configure default routing for unknown offer_ids

## Refund Handling

### Partial Refunds by Offer ID

Process refunds for specific offer_ids:

```json
{
  "offer_id": "MTPL",
  "amount": 5000,
  "reason": "Partial cancellation"
}
```

### Full Refunds

Full refunds will process all transactions for the original payment automatically.

## Important Notes

- Transaction splitting works with all payment methods (cards, bank transfers, etc.)
- Fees are distributed proportionally across split transactions
- Each split transaction maintains full traceability to the original payment
- Split routing rules are used for automatic payouts, not incoming payments
