# Transaction Splitting

## Overview

Transaction splitting allows merchants to automatically split incoming payments into multiple transaction records based on product `offer_id` values. This enables separate tracking and reporting for different product types within a single payment.

**Use Cases:**
- Insurance companies (MTPL, CASCO products)
- Marketplace vendors (different sellers)
- Multi-brand retailers (different product lines)
- Service providers (different service types)

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
      "name": "Premium Service",
      "offer_id": "PREMIUM",
      "unit_price": 100.00,
      "quantity": 1
    },
    {
      "name": "Basic Service",
      "offer_id": "BASIC",
      "unit_price": 200.00,
      "quantity": 1
    }
  ],
  "should_split": true
}
```

⚠️ **Important:** When creating a checkout with `should_split: true`, the sum of all product `unit_price * quantity` values **must equal the total checkout amount**.

**Industry Examples:**
- Insurance: `offer_id: "MTPL"`, `offer_id: "CASCO"`
- Marketplace: `offer_id: "VENDOR_A"`, `offer_id: "VENDOR_B"`
- Retail: `offer_id: "ELECTRONICS"`, `offer_id: "CLOTHING"`

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
          "offer_id": "PREMIUM"
        },
        {
          "transaction_id": "txn_790",
          "amount": 20000,
          "offer_id": "BASIC"
        }
      ]
    }
  }
}
```

## Split Routing Configuration

Split routing rules define **how payouts are distributed** for transactions with different `offer_id`s.  
These rules **cannot be managed via API or dashboard** — they must be requested from our team.  

### How to Set Up Split Routing Rules
To configure or update routing rules, please contact **support** or your **account manager** and provide:  
- `offer_id` (must match your product configuration)  
- Destination **IBAN**  
- **Bank name**  
- Optional **description**  

**Example Request:**  
```json
{
  "offer_id": "PREMIUM",
  "iban": "RO23CITI0000000000000001",
  "bank_name": "Citi Bank Romania",
  "description": "Premium Service Payouts"
}
```

### Default Handling
- If a transaction’s `offer_id` does not have a routing rule, the payout will be directed to your **default settlement account**.  
- All updates must go through our **support team**.  

## Refund Handling

When processing refunds for split transactions, it is **mandatory** to include the `offer_id` in the request body.  
This ensures we know exactly which split transaction should be refunded.  

### Partial Refunds by Offer ID

Process refunds for a specific `offer_id`:

```bash
POST /api/v1/refunds
Content-Type: application/json
Authorization: Bearer your_api_token
```

**Request Body (mandatory `offer_id`):**
```json
{
  "checkout_id": "checkout_123",
  "offer_id": "PREMIUM",
  "amount": 5000,
  "reason": "Partial cancellation",
  "nonce": "random_string",
  "signature": "calculated_signature"
}
```

**Response:**
```json
{
  "id": "refund_456",
  "object": "refund",
  "amount": 5000,
  "currency": "RON",
  "external_id": "checkout_123",
  "status": "pending",
  "metadata": {
    "offer_id": "PREMIUM",
    "transaction_splitting": true
  },
  "created_at": 1640995200
}
```

### Get Split Refund Options
```bash
GET /api/v1/refunds/{checkout_id}/split_options
Authorization: Bearer your_api_token
```

**Response:**
```json
{
  "data": [
    {
      "offer_id": "PREMIUM",
      "product_name": "Premium Service",
      "total_amount": 10000,
      "refunded_amount": 2000,
      "refundable_amount": 8000,
      "can_refund": true
    },
    {
      "offer_id": "BASIC",
      "product_name": "Basic Service",
      "total_amount": 20000,
      "refunded_amount": 0,
      "refundable_amount": 20000,
      "can_refund": true
    }
  ]
}
```

### Full Refunds

Full refunds will process all transactions for the original payment automatically:

```json
{
  "checkout_id": "checkout_123",
  "nonce": "random_string",
  "signature": "calculated_signature"
}
```

## Important Notes

- Transaction splitting works with all payment methods (cards, bank transfers, etc.)
- Fees are distributed proportionally across split transactions
- Each split transaction maintains full traceability to the original payment
- Split routing rules are used for automatic payouts, not incoming payments
