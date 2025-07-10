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

### 2. Configure Split Routing

**Configure IBAN routing for your offer_ids through the merchant dashboard:**

1. **Login to Merchant Dashboard**: Navigate to Settings → Split Routing
2. **Add Routing Rules**: Configure where each offer_id should route funds

**Example Configuration:**
| Offer ID | IBAN | Description |
|----------|------|-------------|
| `MTPL` | `RO23CITI0000000000000001` | MTPL Insurance - Citi Bank Romania |
| `CASCO` | `RO23BTRL0000000000000001` | CASCO Insurance - Banca Transilvania |
| `LIFE` | `RO23INGB0000000000000001` | Life Insurance - ING Bank Romania |

### 3. Product Configuration

Each product in your checkout must include an `offer_id` that matches your configured routing rules:

```json
{
  "name": "MTPL Basic Coverage",
  "amount": 150.00,
  "offer_id": "MTPL"
}
```

> **Important**: The `offer_id` must match exactly with the routing rules configured in your merchant dashboard. If no routing rule is found for an offer_id, the transaction will fail.

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

### Checkout Events

You'll receive **one webhook notification** when the checkout is completed, with split transaction details included:

```json
{
  "event": "checkout.succeeded",
  "data": {
    "object": "checkout",
    "id": "checkout_abc123",
    "external_id": "order_12345",
    "amount": 45000,
    "currency": "RON",
    "redirect_url": "https://yoursite.com/payment/success",
    "customer": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "customer@example.com"
    },
    "payment": {
      "object": "payment",
      "status": "successful",
      "payment_method": "PayU",
      "failure_reason": "",
      "created_at": 1641234567,
      "fee": 2250,
      "net": 42750
    },
    "split_transactions": [
      {
        "transaction_id": "txn_mtpl_456",
        "amount": 15000,
        "offer_id": "MTPL",
        "bank_account": "RO23CITI0000000000000001"
      },
      {
        "transaction_id": "txn_casco_789",
        "amount": 30000,
        "offer_id": "CASCO",
        "bank_account": "RO23BTRL0000000000000001"
      }
    ],
    "metadata": {},
    "status": "succeeded"
  }
}
```

> **Note**:
> - Amounts are in cents (e.g., 45000 = €450.00)
> - `bank_account` field shows the IBAN configured for each offer_id in your split routing rules

### Webhook Handling

Update your webhook handler to process the checkout completion with split transaction details:

```javascript
// Example webhook handler
app.post('/webhooks/payout', (req, res) => {
  const { event, data } = req.body;

  if (event === 'checkout.succeeded') {
    const { id: checkout_id, external_id, split_transactions, status } = data;

    // Check if this is a split transaction checkout
    if (split_transactions && split_transactions.length > 0) {
      // Process each split transaction
      split_transactions.forEach(transaction => {
        const { transaction_id, amount, offer_id, bank_account } = transaction;

        // Update your system based on offer_id
        if (offer_id === 'MTPL') {
          // Handle MTPL transaction completion
          // Note: amount is in cents, convert to currency units
          updateInsurancePolicy(checkout_id, 'MTPL', amount / 100, transaction_id);
        } else if (offer_id === 'CASCO') {
          // Handle CASCO transaction completion
          updateInsurancePolicy(checkout_id, 'CASCO', amount / 100, transaction_id);
        }
      });
    }

    // Mark the overall checkout as complete
    markCheckoutComplete(checkout_id, external_id);
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

## Split Routing Management

### Managing via Merchant Dashboard

1. **Login to Merchant Dashboard**: Navigate to Settings → Split Routing
2. **Add New Rule**: Click "Add Routing Rule"
3. **Configure**: Set offer_id, IBAN, and description
4. **Save**: Rule becomes active immediately

### Managing via API

You can also manage split routing rules programmatically:

#### Create Routing Rule
```json
POST /api/v1/split-routing-rules

{
  "offer_id": "MTPL",
  "iban": "RO23CITI0000000000000001",
  "description": "MTPL Insurance - Citi Bank Romania"
}
```

#### List Routing Rules
```json
GET /api/v1/split-routing-rules
```

#### Update Routing Rule
```json
PUT /api/v1/split-routing-rules/{rule_id}

{
  "iban": "RO23NEUE0000000000000001",
  "description": "MTPL Insurance - New Bank"
}
```

#### Delete Routing Rule
```json
DELETE /api/v1/split-routing-rules/{rule_id}
```

## Error Handling

## Support

For technical integration support or questions about transaction splitting:

- **Email**: tech@payout.com
- **Documentation**: https://developers.payout.com
- **API Reference**: https://postman.payout.one/

For account setup and business questions:
- **Email**: sales@payout.com
- **Account Manager**: Contact your dedicated account manager
