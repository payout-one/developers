# Transaction Splitting Documentation

## Overview

The **Transaction Splitting** feature enables insurance companies to purchase multiple insurance products (MTPL and CASCO) in a single checkout transaction, with each product type being routed to different bank accounts. This functionality maintains the existing pattern of 1 checkout → 1 payment while creating multiple transactions (instead of a single transaction) for different offer_ids.

## Business Context

### Insurance Industry Requirements
- **MTPL (Motor Third Party Liability)**: Mandatory insurance covering third-party damages
- **CASCO (Comprehensive Auto Insurance)**: Optional insurance covering vehicle damages
- **Regulatory Compliance**: Different insurance types must be processed through different financial institutions

### Routing Logic
- **MTPL products** → Citi Bank Romania (`RO23CITI0000000000000001`)
- **CASCO products** → Banca Transilvania (`RO23BTRL0000000000000001`)

## Architecture

### System Components

The transaction splitting feature spans three main services:

1. **payout_api**: Core splitting logic and transaction creation
2. **payout_checkout**: Payment processing and checkout handling
3. **payout_merchant**: Merchant dashboard, reporting, and refund processing
4. **payout_admin**: Feature flag management and administration

### Database Schema

#### Products Enhancement
Products are stored in the `products` JSONB field of the `finance_checkouts` table with the following structure:

```json
{
  "products": [
    {
      "name": "MTPL Basic",
      "amount": 150,
      "offer_id": "MTPL"
    },
    {
      "name": "CASCO Standard",
      "amount": 300,
      "offer_id": "CASCO"
    }
  ]
}
```

#### Transaction Metadata
Split transactions store additional metadata in the `metadata` JSONB field:

```json
{
  "metadata": {
    "transaction_splitting": true,
    "offer_id": "MTPL",
    "products": [
      {
        "name": "MTPL Basic",
        "amount": 150,
        "offer_id": "MTPL"
      }
    ]
  }
}
```

#### Bank Transfers
Each split transaction creates a corresponding `finance_bank_transfers` record linking to the appropriate bank:

- **MTPL**: Links to Citi Bank Romania
- **CASCO**: Links to Banca Transilvania

## Implementation Details

### Feature Flag Control

The feature is controlled by the `transaction_splitting` boolean flag in the account's features:

```elixir
# Enable transaction splitting
account = %Account{
  features: %{
    transaction_splitting: true
  }
}
```

### Core Splitting Logic

#### Decision Logic
```elixir
def should_split?(checkout) do
  # 1. Feature flag must be enabled
  # 2. Multiple unique offer_ids must be present
  # 3. Products must have valid offer_ids
end
```

#### Product Grouping
```elixir
def group_products_by_offer_id(products) do
  # Groups products by offer_id
  # Calculates total amount per offer_id
  # Returns: %{offer_id => %{products: [...], total_amount: amount}}
end
```

#### Transaction Creation
```elixir
def create_split_transactions(checkout, payment, account_customer) do
  # Creates one transaction per offer_id
  # Distributes fees proportionally based on amount
  # Creates bank transfers with correct IBANs
end
```

### Fee Distribution

Fees are distributed proportionally based on the amount percentage:

```elixir
# Example: Total amount = 500, MTPL = 200, CASCO = 300, Total fee = 25
mtpl_fee = 25 * (200 / 500) = 10
casco_fee = 25 * (300 / 500) = 15
```

### IBAN Routing

```elixir
def get_iban_for_offer_id(offer_id) do
  case offer_id do
    "MTPL" -> "RO23CITI0000000000000001"
    "CASCO" -> "RO23BTRL0000000000000001"
    _ -> nil
  end
end
```

## API Usage

### Checkout Creation

To create a checkout with transaction splitting, include `offer_id` in the products:

```json
{
  "external_id": "checkout_123",
  "amount": 500,
  "currency": "EUR",
  "products": [
    {
      "name": "MTPL Basic",
      "amount": 200,
      "offer_id": "MTPL"
    },
    {
      "name": "CASCO Standard",
      "amount": 300,
      "offer_id": "CASCO"
    }
  ]
}
```

### Payment Processing

The payment processing remains unchanged from the client perspective. The system automatically detects when splitting should occur and creates multiple transactions.

### Webhook Notifications

Webhook notifications are sent for each split transaction individually:

```json
{
  "event": "transaction.succeeded",
  "data": {
    "transaction_id": "txn_123",
    "offer_id": "MTPL",
    "amount": 200,
    "products": [
      {
        "name": "MTPL Basic",
        "amount": 200,
        "offer_id": "MTPL"
      }
    ]
  }
}
```

## Merchant Dashboard

### Transaction Display

Split transactions are clearly identified in the merchant dashboard:

- **Split transaction badge**: Visual indicator for split transactions
- **Offer ID display**: Shows which offer_id the transaction represents
- **Product breakdown**: Detailed view of products in each split transaction
- **Target IBAN**: Shows the destination bank account

### Transaction Details

The transaction detail view includes:

```
Transaction Type: Payment (Split - MTPL)
Offer ID: MTPL
Target IBAN: RO23CITI0000000000000001
Products:
  - MTPL Basic: €150.00
  - MTPL Premium: €50.00
Total Amount: €200.00
```

## Refund Processing

### Split Transaction Refunds

Split transactions support partial refunds by offer_id:

1. **Offer Selection**: Choose which offer_id to refund
2. **Amount Validation**: Ensure refund amount doesn't exceed offer total
3. **Partial Refunds**: Support multiple partial refunds per offer_id

### Refund UI

The refund interface shows:

```
□ MTPL Basic (MTPL)
  Total: €200.00
  Refunded: €0.00
  Available: €200.00

□ CASCO Standard (CASCO)
  Total: €300.00
  Refunded: €0.00
  Available: €300.00
```

### Refund Logic

```elixir
def refund_split_transaction(transaction, attrs, user) do
  # Validates offer_id exists in transaction
  # Checks refund amount doesn't exceed available amount
  # Creates refund withdrawal with offer_id metadata
end
```

## Reporting

### Transaction Reports

Split transactions appear in reports with enhanced information:

- **Reference**: Includes offer_id (e.g., "REF_123 (MTPL)")
- **IBAN**: Shows destination bank account
- **Product Details**: Breakdown of products in each transaction

### Balance Calculations

Balance calculations properly handle split transactions:

- Each split transaction contributes to the total balance
- Fees are distributed proportionally across split transactions
- Refunds are tracked per offer_id

## Error Handling

### Common Scenarios

1. **Feature Flag Disabled**: Falls back to standard payment processing
2. **Single Offer ID**: Creates standard transaction (no splitting)
3. **Unknown Offer ID**: Skips products with unknown offer_ids
4. **Mixed Products**: Only processes products with valid offer_ids

### Error Messages

```elixir
# Invalid offer_id in refund
{:error, changeset} = refund_split_transaction(transaction, %{offer_id: "INVALID"}, user)
# changeset.errors[:offer_id] = ["Offer ID not found in transaction"]

# Refund amount exceeds available
{:error, changeset} = refund_split_transaction(transaction, %{amount: 1000}, user)
# changeset.errors[:amount] = ["Amount exceeds available refund amount"]
```

## Testing

### Test Coverage

The feature includes comprehensive tests for:

1. **Unit Tests**: TransactionSplitter module functionality
2. **Integration Tests**: Full payment flow from checkout to transaction creation
3. **Refund Tests**: Split transaction refund processing
4. **UI Tests**: Merchant dashboard display and interaction
5. **Error Handling**: Edge cases and error scenarios

### Test Data

```elixir
# Test checkout with split products
checkout = insert(:checkout,
  products: [
    %{name: "MTPL Basic", amount: 100, offer_id: "MTPL"},
    %{name: "CASCO Standard", amount: 200, offer_id: "CASCO"}
  ]
)
```

## Configuration

### Feature Flag Management

Enable transaction splitting in payout_admin:

1. Navigate to Account Settings
2. Go to Features section
3. Enable "Transaction Splitting"
4. Description: "Enable splitting transactions by products for insurance companies"

### Bank Configuration

The system automatically creates bank records for:

- **Citi Bank Romania**: `RO23CITI0000000000000001` (BIC: CITIROBU)
- **Banca Transilvania**: `RO23BTRL0000000000000001` (BIC: BTRLRO22)

## Performance Considerations

### Database Impact

- **Additional Transactions**: Creates multiple transaction records per payment
- **Metadata Storage**: Stores additional JSON metadata per transaction
- **Bank Transfers**: Creates additional bank transfer records

### Optimization

- **Batch Processing**: Bank transfers are created in batches
- **Indexing**: Ensure proper indexing on metadata fields for queries
- **Caching**: Feature flag status is cached per account

## Security Considerations

### Data Validation

- **Offer ID Validation**: Only allows known offer_ids (MTPL, CASCO)
- **Amount Validation**: Ensures split amounts sum to total
- **Permission Checks**: Refunds require proper user permissions

### Audit Trail

- **Transaction Metadata**: Complete audit trail of splitting decisions
- **User Tracking**: All refunds track the initiating user
- **Webhook Logs**: Complete log of webhook notifications sent

## Migration Guide

### Existing Accounts

1. **Feature Flag**: Enable transaction splitting feature flag
2. **Product Updates**: Add offer_id to existing product data
3. **Testing**: Verify splitting behavior with test transactions
4. **Monitoring**: Monitor transaction creation and routing

### Rollback Plan

1. **Feature Flag**: Disable transaction splitting feature flag
2. **Fallback**: System automatically falls back to standard processing
3. **Data Integrity**: Existing split transactions remain valid
4. **Reporting**: Historical split transactions remain visible

## Troubleshooting

### Common Issues

1. **No Splitting Occurs**
   - Check feature flag is enabled
   - Verify multiple offer_ids are present
   - Ensure offer_ids are valid (MTPL, CASCO)

2. **Incorrect IBAN Routing**
   - Verify offer_id mapping in TransactionSplitter
   - Check bank records are created correctly

3. **Fee Distribution Issues**
   - Verify proportional calculation logic
   - Check decimal precision handling

### Debug Information

```elixir
# Check if transaction should split
TransactionSplitter.should_split?(checkout)

# View grouped products
TransactionSplitter.group_products_by_offer_id(products)

# Check IBAN mapping
TransactionSplitter.get_iban_for_offer_id("MTPL")
```

## Support

For questions or issues with transaction splitting:

1. **Technical Issues**: Check logs in payout_api and payout_checkout
2. **Business Questions**: Contact the EFM project team
3. **Feature Requests**: Submit through the standard feature request process

## Changelog

### Version 1.0 (Initial Release)
- Basic transaction splitting functionality
- MTPL and CASCO offer_id support
- Merchant dashboard enhancements
- Split transaction refund processing
- Comprehensive test coverage
- Documentation and troubleshooting guides

### Future Enhancements
- Support for additional insurance product types
- Advanced fee distribution strategies
- Enhanced reporting and analytics
- API endpoint for split transaction management
