# Transaction Splitting

Split payments allow insurance companies and other businesses to process multiple product types in a single checkout while routing payments to different bank accounts automatically.

## Overview

Transaction splitting enables you to:
- **Single Checkout Experience**: Customers complete one checkout for multiple products
- **Automatic Routing**: Different product types are routed to different bank accounts
- **Separate Reporting**: View transactions separated by product type
- **Individual Refunds**: Refund specific products independently

### Use Cases

**Insurance Industry**
- **MTPL (Motor Third Party Liability)**: Mandatory insurance → Routes to Bank A
- **CASCO (Comprehensive Auto Insurance)**: Optional insurance → Routes to Bank B

**E-commerce Platforms**
- **Digital Products**: Software licenses → Routes to Tech Account
- **Physical Products**: Merchandise → Routes to Fulfillment Account

## Getting Started

### 1. Feature Activation

Contact your account manager to enable transaction splitting for your account.

### 2. Product Configuration

Each product in your checkout must include an `offer_id` to identify the product type:

```json
{
  "name": "MTPL Basic Coverage",
  "amount": 150.00,
  "offer_id": "MTPL"
}
```

### 3. Supported Product Types

| Product Type | offer_id | Routes To |
|--------------|----------|-----------|
| MTPL Insurance | `"MTPL"` | Citi Bank Romania |
| CASCO Insurance | `"CASCO"` | Banca Transilvania |

## API Integration

### Creating Split Checkout

Set `should_split: true` to explicitly enable splitting:

> **Important**: Transaction splitting will only occur when `should_split: true` is explicitly set. The system will not automatically detect or enable splitting based on product types.

```json
POST /api/v1/checkouts

{
  "external_id": "order_12345",
  "amount": 450.00,
  "currency": "RON",
  "should_split": true,
  "products": [
    {
      "name": "MTPL Basic Coverage",
      "amount": 150.00,
      "offer_id": "MTPL"
    },
    {
      "name": "CASCO Premium Coverage",
      "amount": 300.00,
      "offer_id": "CASCO"
    }
  ],
  "customer": {
    "email": "customer@example.com",
    "name": "John Doe"
  },
  "redirect_url": "https://yoursite.com/payment/success"
}
```



### Checkout Response

```json
{
  "id": "checkout_abc123",
  "status": "processing",
  "amount": 450.00,
  "currency": "RON",
  "should_split": true,
  "external_id": "order_12345",
  "payment_url": "https://checkout.payout.com/checkout_abc123",
  "products": [
    {
      "name": "MTPL Basic Coverage",
      "amount": 150.00,
      "offer_id": "MTPL"
    },
    {
      "name": "CASCO Premium Coverage",
      "amount": 300.00,
      "offer_id": "CASCO"
    }
  ]
}
```

### Payment Processing

The payment experience for your customers remains unchanged:
1. Customer completes single checkout
2. Makes one payment for total amount (€450.00)
3. System automatically splits into separate transactions
4. Each transaction routes to appropriate bank account

## Webhooks

### Transaction Events

You'll receive separate webhook notifications for each split transaction:

#### MTPL Transaction
```json
{
  "event": "transaction.succeeded",
  "data": {
    "transaction_id": "txn_mtpl_456",
    "checkout_id": "checkout_abc123",
    "amount": 150.00,
    "currency": "RON",
    "offer_id": "MTPL",
    "products": [
      {
        "name": "MTPL Basic Coverage",
        "amount": 150.00,
        "offer_id": "MTPL"
      }
    ],
    "bank_account": "RO23CITI0000000000000001"
  }
}
```

#### CASCO Transaction
```json
{
  "event": "transaction.succeeded",
  "data": {
    "transaction_id": "txn_casco_789",
    "checkout_id": "checkout_abc123",
    "amount": 300.00,
    "currency": "RON",
    "offer_id": "CASCO",
    "products": [
      {
        "name": "CASCO Premium Coverage",
        "amount": 300.00,
        "offer_id": "CASCO"
      }
    ],
    "bank_account": "RO23BTRL0000000000000001"
  }
}
```

### Webhook Handling

Update your webhook handler to process multiple transactions per checkout:

```javascript
// Example webhook handler
app.post('/webhooks/payout', (req, res) => {
  const { event, data } = req.body;

  if (event === 'transaction.succeeded') {
    const { checkout_id, offer_id, amount } = data;

    // Update your system based on offer_id
    if (offer_id === 'MTPL') {
      // Handle MTPL transaction completion
      updateInsurancePolicy(checkout_id, 'MTPL', amount);
    } else if (offer_id === 'CASCO') {
      // Handle CASCO transaction completion
      updateInsurancePolicy(checkout_id, 'CASCO', amount);
    }
  }

  res.status(200).send('OK');
});
```

## Refunds

### Product-Specific Refunds

Refund specific products using the transaction ID and offer_id:

```json
POST /api/v1/refunds

{
  "transaction_id": "txn_mtpl_456",
  "amount": 150.00,
  "offer_id": "MTPL",
  "reason": "Customer cancellation"
}
```

### Partial Refunds

You can issue multiple partial refunds for the same product:

```json
POST /api/v1/refunds

{
  "transaction_id": "txn_mtpl_456",
  "amount": 50.00,
  "offer_id": "MTPL",
  "reason": "Partial coverage adjustment"
}
```

### Refund Response

```json
{
  "id": "refund_xyz789",
  "status": "succeeded",
  "amount": 50.00,
  "currency": "RON",
  "transaction_id": "txn_mtpl_456",
  "offer_id": "MTPL"
}
```

## Reporting & Analytics

### Transaction Queries

Query transactions by offer_id to get product-specific reports:

```json
GET /api/v1/transactions?offer_id=MTPL&date_from=2024-01-01&date_to=2024-01-31
```

### Response
```json
{
  "transactions": [
    {
      "id": "txn_mtpl_456",
      "amount": 150.00,
      "offer_id": "MTPL",
      "status": "succeeded",
      "created_at": "2024-01-15T10:30:00Z",
      "bank_account": "RO23CITI0000000000000001"
    }
  ],
  "total_count": 1,
  "total_amount": 150.00
}
```

## Testing

### Test Environment

Use test offer_ids in your development environment:

```json
{
  "products": [
    {
      "name": "Test MTPL Product",
      "amount": 100.00,
      "offer_id": "TEST_MTPL"
    },
    {
      "name": "Test CASCO Product",
      "amount": 200.00,
      "offer_id": "TEST_CASCO"
    }
  ]
}
```

### Test Cards

Use standard Payout test cards for payment testing. Split functionality works with all supported payment methods.

## Error Handling

### Common Scenarios

| Scenario | Behavior |
|----------|----------|
| Feature not enabled | Standard single transaction created |
| Unknown offer_id | Product skipped, others processed normally |
| Single product type | Standard single transaction created |
| Mixed valid/invalid offer_ids | Only valid products processed |

### Error Responses

```json
{
  "error": "invalid_offer_id",
  "message": "Offer ID 'INVALID' is not supported",
  "code": "SPLIT_001"
}
```

## Support

For technical integration support or questions about transaction splitting:

- **Email**: developers@payout.com
- **Documentation**: https://developers.payout.com
- **API Reference**: https://developers.payout.com/api

For account setup and business questions:
- **Email**: sales@payout.com
- **Account Manager**: Contact your dedicated account manager
